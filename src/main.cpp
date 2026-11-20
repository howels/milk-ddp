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
#include <csignal>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>

namespace {

std::atomic<bool> g_stop{false};

void on_signal(int)
{
    g_stop.store(true, std::memory_order_relaxed);
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

        if (!cfg.preset.empty()) {
            projectm_load_preset_file(pm.get(), cfg.preset.c_str(), false);
        } else if (added > 0) {
            projectm_playlist_set_position(playlist.get(), 0, true);
        } else {
            projectm_load_preset_file(pm.get(), "idle://", false);
        }

        auto audio = make_audio_source(cfg.audio, cfg.sample_rate);
        DdpSender ddp(cfg.ddp_host, cfg.ddp_port);

        const unsigned int pcm_per_frame =
            static_cast<unsigned int>(audio->sample_rate() / std::max(1, cfg.fps));
        const unsigned int max_pcm = projectm_pcm_get_max_samples();
        const unsigned int feed = std::min(pcm_per_frame, max_pcm);

        std::vector<float> pcm;
        std::vector<unsigned char> rgb(static_cast<std::size_t>(cfg.width) * cfg.height * 3);

        if (!cfg.quiet) {
            char* ver = projectm_get_version_string();
            std::cerr << "libprojectM " << (ver != nullptr ? ver : "unknown") << "\n"
                      << "GL " << gl.renderer_string() << "\n"
                      << "render " << cfg.width << "x" << cfg.height << " @ " << cfg.fps
                      << " fps → DDP " << cfg.ddp_host << ":" << cfg.ddp_port << "\n"
                      << "presets in playlist: " << projectm_playlist_size(playlist.get()) << "\n";
            if (ver != nullptr) {
                projectm_free_string(ver);
            }
        }

        const auto frame_dt = std::chrono::duration<double>(1.0 / cfg.fps);
        auto next = std::chrono::steady_clock::now();
        int frame = 0;

        while (!g_stop.load(std::memory_order_relaxed)) {
            if (cfg.frames > 0 && frame >= cfg.frames) {
                break;
            }

            audio->fill(pcm, feed);
            if (!pcm.empty()) {
                projectm_pcm_add_float(pm.get(), pcm.data(), feed, PROJECTM_STEREO);
            }

            gl.bind_default();
            projectm_opengl_render_frame(pm.get());
            gl.read_rgb(rgb.data());
            ddp.send_rgb_frame(rgb.data(), static_cast<std::size_t>(cfg.width) * cfg.height);

            ++frame;
            if (cfg.progress && !cfg.quiet && (frame == 1 || frame % cfg.fps == 0)) {
                std::cerr << "frames " << frame << "\n";
            }

            next += std::chrono::duration_cast<std::chrono::steady_clock::duration>(frame_dt);
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
