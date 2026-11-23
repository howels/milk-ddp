/* SPDX-License-Identifier: GPL-3.0-or-later
 * Copyright (C) 2026 milk-ddp contributors
 */
#include "audio.hpp"
#include "cli.hpp"
#include "ddp.hpp"
#include "egl_offscreen.hpp"
#include "projectm_props.hpp"

#include <projectM-4/projectM.h>
#include <projectM-4/playlist.h>

#include <algorithm>
#include <atomic>
#include <chrono>
#include <cmath>
#include <csignal>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>

#include <unistd.h>

namespace {

std::atomic<bool> g_stop{false};

float pcm_peak_abs(const std::vector<float>& pcm)
{
    float peak = 0.0f;
    for (float s : pcm) {
        const float a = std::fabs(s);
        if (a > peak) {
            peak = a;
        }
    }
    return peak;
}

void on_signal(int)
{
    g_stop.store(true, std::memory_order_relaxed);
}

std::string preset_display_name(const std::string& path)
{
    if (path.empty()) {
        return "(none)";
    }
    if (path == "idle://") {
        return "idle";
    }
    const auto slash = path.find_last_of('/');
    if (slash == std::string::npos) {
        return path;
    }
    return path.substr(slash + 1);
}

void print_preset_line(const std::string& path)
{
    std::cerr << "preset " << preset_display_name(path) << "  " << path << "\n";
}

struct PlaylistSwitchContext {
    projectm_playlist* playlist = nullptr;
    bool log_presets = false;
    bool transition_half_fps = false;
    double soft_cut_seconds = 3.0;
    // Soft-cut window: render loop paces at fps/2 until this time (steady_clock).
    std::chrono::steady_clock::time_point soft_cut_until{};
};

void on_playlist_preset_switched(bool is_hard_cut, unsigned int index, void* user_data)
{
    auto* ctx = static_cast<PlaylistSwitchContext*>(user_data);
    if (ctx == nullptr) {
        return;
    }
    if (ctx->transition_half_fps) {
        if (!is_hard_cut && ctx->soft_cut_seconds > 0.0) {
            // Small grace so the last blend frames still get the half-rate budget.
            ctx->soft_cut_until = std::chrono::steady_clock::now() +
                std::chrono::duration_cast<std::chrono::steady_clock::duration>(
                    std::chrono::duration<double>(ctx->soft_cut_seconds + 0.05));
        } else {
            ctx->soft_cut_until = {};
        }
    }
    if (!ctx->log_presets || ctx->playlist == nullptr) {
        return;
    }
    char* item = projectm_playlist_item(ctx->playlist, index);
    if (item == nullptr) {
        return;
    }
    print_preset_line(item);
    projectm_playlist_free_string(item);
}

void write_ppm(const std::string& path, int width, int height, const unsigned char* rgb)
{
    std::ofstream out(path, std::ios::binary);
    if (!out) {
        throw std::runtime_error("cannot write " + path);
    }
    out << "P6\n" << width << " " << height << "\n255\n";
    out.write(reinterpret_cast<const char*>(rgb),
              static_cast<std::streamsize>(width) * height * 3);
}

struct ProjectMDeleter {
    void operator()(projectm* p) const noexcept
    {
        if (p != nullptr) {
            projectm_destroy(p);
        }
    }
};

struct PlaylistDeleter {
    void operator()(projectm_playlist* p) const noexcept
    {
        if (p != nullptr) {
            projectm_playlist_destroy(p);
        }
    }
};

using ProjectMPtr = std::unique_ptr<projectm, ProjectMDeleter>;
using PlaylistPtr = std::unique_ptr<projectm_playlist, PlaylistDeleter>;

}  // namespace

int main(int argc, char** argv)
{
    try {
        const Config cfg = parse_args(argc, argv);
        if (cfg.list_audio) {
            return list_audio_devices();
        }

        std::signal(SIGINT, on_signal);
        std::signal(SIGTERM, on_signal);

        OffscreenGL gl;
        gl.create(cfg.width, cfg.height, cfg.software_gl);

        ProjectMPtr pm(projectm_create());
        if (!pm) {
            throw std::runtime_error(
                "projectm_create() returned null; OpenGL 3.3 context is missing or unusable");
        }

        PlaylistPtr playlist(projectm_playlist_create(pm.get()));
        if (!playlist) {
            throw std::runtime_error("projectm_playlist_create() failed");
        }

        if (!cfg.texture_paths.empty()) {
            std::vector<const char*> ptrs;
            ptrs.reserve(cfg.texture_paths.size());
            for (const auto& p : cfg.texture_paths) {
                ptrs.push_back(p.c_str());
            }
            projectm_set_texture_search_paths(pm.get(), ptrs.data(), ptrs.size());
        }

        apply_projectm_properties(pm.get(), playlist.get(), cfg);

        unsigned int added = 0;
        for (const auto& path : cfg.preset_paths) {
            added += projectm_playlist_add_path(playlist.get(), path.c_str(), true, false);
        }
        if (added > 0) {
            // Filesystem scan order is not stable; sort so non-shuffle playback
            // walks presets in ascending full-path order.
            projectm_playlist_sort(playlist.get(), 0, added, SORT_PREDICATE_FULL_PATH,
                                   SORT_ORDER_ASCENDING);
        }

        std::string single_preset;
        if (!cfg.preset.empty()) {
            single_preset = cfg.preset;
            projectm_load_preset_file(pm.get(), cfg.preset.c_str(), false);
        } else if (added > 0) {
            projectm_playlist_set_position(playlist.get(), 0, true);
        } else {
            single_preset = "idle://";
            projectm_load_preset_file(pm.get(), "idle://", false);
        }

        auto audio = make_audio_source(cfg.audio, cfg.sample_rate, cfg.audio_gain);
        DdpSender ddp(cfg.ddp_host, cfg.ddp_port, cfg.close_on_disconnect);

        const unsigned int pcm_per_frame =
            static_cast<unsigned int>(audio->sample_rate() / std::max(1, cfg.fps));
        const unsigned int max_pcm = projectm_pcm_get_max_samples();
        const unsigned int feed = std::min(pcm_per_frame, max_pcm);

        std::vector<float> pcm;
        std::vector<unsigned char> rgb(static_cast<std::size_t>(cfg.width) * cfg.height * 3);

        PlaylistSwitchContext switch_ctx;
        switch_ctx.playlist = playlist.get();
        switch_ctx.log_presets = !cfg.quiet;
        switch_ctx.transition_half_fps = cfg.transition_half_fps;
        switch_ctx.soft_cut_seconds = projectm_get_soft_cut_duration(pm.get());

        if (!cfg.quiet) {
            char* ver = projectm_get_version_string();
            std::cerr << "libprojectM " << (ver != nullptr ? ver : "unknown") << "\n"
                      << "GL " << gl.renderer_string() << "\n"
                      << "render " << cfg.width << "x" << cfg.height << " @ " << cfg.fps
                      << " fps → DDP " << cfg.ddp_host << ":" << cfg.ddp_port
                      << " (" << ddp.peer() << ")\n"
                      << "presets in playlist: " << projectm_playlist_size(playlist.get())
                      << "  shuffle=" << (cfg.shuffle ? "on" : "off")
                      << "  duration=" << projectm_get_preset_duration(pm.get()) << "s"
                      << "  soft_cut=" << projectm_get_soft_cut_duration(pm.get()) << "s\n"
                      << "audio " << cfg.audio << "  gain=" << cfg.audio_gain
                      << "  transition_half_fps="
                      << (cfg.transition_half_fps ? "on" : "off")
                      << "  warm_presets=" << (cfg.warm_presets ? "on" : "off")
                      << "  pause_when_silent="
                      << (cfg.pause_when_silent ? "on" : "off");
            if (cfg.pause_when_silent) {
                std::cerr << " (hold=" << cfg.silence_hold
                          << "s thr=" << cfg.silence_threshold
                          << " black=" << (cfg.black_on_silence ? "on" : "off")
                          << ")";
            }
            std::cerr << "\n";
            if (!single_preset.empty()) {
                print_preset_line(single_preset);
            } else if (added > 0) {
                char* item = projectm_playlist_item(playlist.get(), 0);
                if (item != nullptr) {
                    print_preset_line(item);
                    projectm_playlist_free_string(item);
                }
            }
            if (ver != nullptr) {
                projectm_free_string(ver);
            }
        }

        // Soft cuts call Preset::Initialize() (warp/comp GLSL compile) on the
        // switch — a multi-hundred-ms hitch on Mali. Walk the playlist once with
        // hard cuts so Mesa can write its on-disk shader cache first.
        if (cfg.warm_presets && cfg.preset.empty() && added > 0) {
            const uint32_t n = projectm_playlist_size(playlist.get());
            const bool warm_tty = !cfg.quiet && isatty(STDERR_FILENO) == 1;
            if (!cfg.quiet) {
                std::cerr << "caching shaders for " << n
                          << " playlist preset(s) (hard cut, 1 frame each; DDP off)…\n";
            }
            const auto warm_start = std::chrono::steady_clock::now();
            for (uint32_t i = 0; i < n && !g_stop.load(std::memory_order_relaxed); ++i) {
                projectm_playlist_set_position(playlist.get(), i, true);
                // One render is enough to run Initialize() / GLSL compile.
                // Skip readback and DDP so the matrix stays dark during warm-up.
                audio->fill(pcm, feed);
                if (!pcm.empty()) {
                    projectm_pcm_add_float(pm.get(), pcm.data(), feed, PROJECTM_STEREO);
                }
                gl.bind_default();
                projectm_opengl_render_frame(pm.get());
                if (!cfg.quiet) {
                    const double elapsed = std::chrono::duration<double>(
                                               std::chrono::steady_clock::now() - warm_start)
                                               .count();
                    const double per = elapsed / static_cast<double>(i + 1);
                    const double remain = per * static_cast<double>(n - i - 1);
                    const int pct = static_cast<int>(
                        (100.0 * static_cast<double>(i + 1)) / static_cast<double>(n));
                    std::string name = "(unknown)";
                    char* item = projectm_playlist_item(playlist.get(), i);
                    if (item != nullptr) {
                        name = preset_display_name(item);
                        projectm_playlist_free_string(item);
                    }
                    std::ostringstream line;
                    line << "shader cache " << (i + 1) << "/" << n << " (" << pct << "%)  "
                         << name << "  " << std::fixed << std::setprecision(1) << elapsed
                         << "s elapsed";
                    if (i + 1 < n) {
                        line << ", ~" << remain << "s left";
                    }
                    if (warm_tty) {
                        std::cerr << '\r' << line.str() << "    " << std::flush;
                    } else {
                        std::cerr << line.str() << "\n";
                    }
                }
            }
            if (!cfg.quiet && warm_tty) {
                std::cerr << "\n";
            }
            projectm_playlist_set_position(playlist.get(), 0, true);
            if (!cfg.quiet) {
                const double secs = std::chrono::duration<double>(
                                        std::chrono::steady_clock::now() - warm_start)
                                        .count();
                std::cerr << "shader cache ready (" << n << " presets in " << std::fixed
                          << std::setprecision(1) << secs << "s)\n";
                char* item = projectm_playlist_item(playlist.get(), 0);
                if (item != nullptr) {
                    print_preset_line(item);
                    projectm_playlist_free_string(item);
                }
            }
        }

        // Register after warm so startup hard cuts do not spam preset lines /
        // start a soft-cut half-fps window.
        if (cfg.transition_half_fps || !cfg.quiet) {
            projectm_playlist_set_preset_switched_event_callback(
                playlist.get(), &on_playlist_preset_switched, &switch_ctx);
        }

        const auto frame_dt = std::chrono::duration<double>(1.0 / cfg.fps);
        const auto idle_poll_dt = std::chrono::duration<double>(0.2);
        auto next = std::chrono::steady_clock::now();
        auto fps_mark = next;
        auto silence_since = next;  // last time PCM was above threshold
        bool render_paused = false;
        int frame = 0;
        int fps_frames = 0;

        while (!g_stop.load(std::memory_order_relaxed)) {
            if (cfg.frames > 0 && frame >= cfg.frames) {
                break;
            }

            const auto now_pre = std::chrono::steady_clock::now();
            const bool in_soft_cut = cfg.transition_half_fps &&
                switch_ctx.soft_cut_until.time_since_epoch().count() != 0 &&
                now_pre < switch_ctx.soft_cut_until;
            const unsigned int this_feed =
                in_soft_cut ? std::min(max_pcm, feed * 2u) : feed;

            // While paused we only wake at 5 Hz. Drain ~one poll-interval of PCM
            // so silence detection sees current audio instead of a backlog of
            // zeros left when capture outran the slow poll (common when the
            // monitor was silent from process start).
            const bool catching_up = render_paused;
            float peak = 0.0f;
            if (catching_up) {
                audio->nudge_while_paused();
                const unsigned int catchup = static_cast<unsigned int>(
                    std::max(1, audio->sample_rate() / 5));
                unsigned int got = 0;
                while (got < catchup) {
                    const unsigned int chunk = std::min(max_pcm, catchup - got);
                    audio->fill(pcm, chunk);
                    peak = std::max(peak, pcm_peak_abs(pcm));
                    got += chunk;
                }
            } else {
                audio->fill(pcm, this_feed);
                peak = pcm_peak_abs(pcm);
            }
            const bool silent = peak < cfg.silence_threshold;
            if (!silent) {
                silence_since = now_pre;
            }
            const bool want_pause = cfg.pause_when_silent && silent &&
                std::chrono::duration<double>(now_pre - silence_since).count() >=
                    cfg.silence_hold;
            if (want_pause != render_paused) {
                if (want_pause && cfg.black_on_silence) {
                    std::fill(rgb.begin(), rgb.end(), static_cast<unsigned char>(0));
                    ddp.send_rgb_frame(rgb.data(),
                                       static_cast<std::size_t>(cfg.width) * cfg.height);
                }
                render_paused = want_pause;
                if (!cfg.quiet) {
                    std::cerr << (render_paused ? "audio idle; render paused\n"
                                                : "audio live; render resumed\n");
                }
            }

            if (!render_paused) {
                if (catching_up) {
                    // Catch-up left pcm as the last drained chunk; take a fresh
                    // frame-sized buffer for projectM now that we are live again.
                    audio->fill(pcm, this_feed);
                }
                if (!pcm.empty()) {
                    projectm_pcm_add_float(pm.get(), pcm.data(), this_feed, PROJECTM_STEREO);
                }

                gl.bind_default();
                projectm_opengl_render_frame(pm.get());
                gl.read_rgb(rgb.data());
                ddp.send_rgb_frame(rgb.data(),
                                   static_cast<std::size_t>(cfg.width) * cfg.height);
            }

            ++frame;
            ++fps_frames;
            if (cfg.progress && !cfg.quiet && frame % cfg.fps == 0) {
                const auto now_fps = std::chrono::steady_clock::now();
                const double elapsed =
                    std::chrono::duration<double>(now_fps - fps_mark).count();
                const double actual_fps =
                    elapsed > 0.0 ? static_cast<double>(fps_frames) / elapsed : 0.0;
                std::cerr << "render " << cfg.width << "x" << cfg.height << " @ "
                          << std::fixed << std::setprecision(1) << actual_fps << "/"
                          << cfg.fps << " fps → DDP " << cfg.ddp_host << ":"
                          << cfg.ddp_port << " (" << ddp.peer() << ")"
                          << (render_paused ? "  [paused]" : "") << "\n";
                fps_mark = now_fps;
                fps_frames = 0;
            }

            const auto step = render_paused
                                  ? idle_poll_dt
                                  : (in_soft_cut ? frame_dt * 2.0 : frame_dt);
            next += std::chrono::duration_cast<std::chrono::steady_clock::duration>(step);
            const auto now = std::chrono::steady_clock::now();
            if (next > now) {
                std::this_thread::sleep_until(next);
            } else {
                next = now;
            }
        }

        if (!cfg.dump_ppm.empty()) {
            write_ppm(cfg.dump_ppm, cfg.width, cfg.height, rgb.data());
        }

        return 0;
    } catch (const std::exception& ex) {
        std::cerr << "milk-ddp: " << ex.what() << "\n";
        return 1;
    }
}
