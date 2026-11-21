#include "cli.hpp"

#include <cstdlib>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <string>

void print_usage()
{
    std::cerr
        << "milk-ddp — headless projectM renderer, DDP output to a WLED matrix\n"
        << "\n"
        << "Usage: milk-ddp [options]\n"
        << "\n"
        << "  --width, -W N            Render width in pixels (default 128)\n"
        << "  --height, -H N           Render height in pixels (default 128)\n"
        << "  --ddp HOST[:PORT]        DDP destination (default 127.0.0.1:4048)\n"
        << "  --fps N                  Frames per second (default 30)\n"
        << "  --preset-path DIR        Recursively scan for .milk presets (repeatable)\n"
        << "  --texture-path DIR       Texture search path (repeatable)\n"
        << "  --preset FILE|idle://    Load one preset instead of cycling the playlist\n"
        << "  --audio SPEC             sine | pulse | pulse:SOURCE | alsa | alsa:DEVICE\n"
        << "                           | file:PATH | stdin  (default sine)\n"
        << "  --audio-gain F           Linear amplitude (default 1.0). Pulse/PipeWire:\n"
        << "                           record-stream soft volume; else scale in fill().\n"
        << "                           Quiet monitors: try 1.5–4.0\n"
        << "  --list-audio             List Pulse and ALSA capture devices and exit\n"
        << "  --sample-rate N          PCM sample rate for sine/stdin (default 44100)\n"
        << "  --frames N               Render N frames then exit (0 = until SIGINT)\n"
        << "  --dump-ppm FILE          Write the last RGB frame as a PPM image\n"
        << "  --software-gl            Force Mesa llvmpipe (no GPU, no display)\n"
        << "  --close-on-disconnect    Exit if the DDP endpoint is offline (default: log\n"
        << "                           \"DDP endpoint offline\" and keep rendering)\n"
        << "  --shuffle                Randomise playlist selection (off by default)\n"
        << "  --no-shuffle             Play presets in alphabetical path order (default)\n"
        << "  --preset-duration SEC    Seconds each playlist preset is shown\n"
        << "                           before the next transition (default 30)\n"
        << "  --switch-delay SEC       Alias for --preset-duration\n"
        << "  --quiet                  Suppress startup status, preset lines, and progress\n"
        << "  --progress               Print periodic status with measured fps (off by default)\n"
        << "  --transition-half-fps    During soft cuts, render at fps/2 (off by default).\n"
        << "                           Matches ~2× GPU cost of blending both presets.\n"
        << "  --no-transition-half-fps Disable --transition-half-fps (default)\n"
        << "  --warm-presets           At startup, hard-cut through the playlist and\n"
        << "                           cache warp/comp shaders (default for playlists).\n"
        << "                           Prints progress on stderr while warming.\n"
        << "  --no-warm-presets        Skip startup shader warm-up\n"
        << "  --set KEY=VALUE          projectM property (repeatable). Keys:\n"
        << "                           beat_sensitivity, hard_cut_duration,\n"
        << "                           hard_cut_enabled, hard_cut_sensitivity,\n"
        << "                           soft_cut_duration, preset_duration,\n"
        << "                           mesh_size (WxH), aspect_correction,\n"
        << "                           easter_egg, preset_locked, shuffle\n"
        << "  --help                   Show this help\n";
}

static bool starts_with(const char* s, const char* p)
{
    return std::strncmp(s, p, std::strlen(p)) == 0;
}

static std::string require_value(int& i, int argc, char** argv, const char* opt)
{
    if (i + 1 >= argc) {
        throw std::runtime_error(std::string(opt) + " requires a value");
    }
    return argv[++i];
}

static int parse_int_range(const std::string& s, const char* name, long min, long max)
{
    char* end = nullptr;
    const long v = std::strtol(s.c_str(), &end, 10);
    if (end == s.c_str() || *end != '\0' || v < min || v > max) {
        throw std::runtime_error(std::string("invalid ") + name + ": " + s);
    }
    return static_cast<int>(v);
}

static int parse_dimension(const std::string& s, const char* name)
{
    return parse_int_range(s, name, 1, 4096);
}

static double parse_positive_seconds(const std::string& s, const char* name)
{
    char* end = nullptr;
    const double v = std::strtod(s.c_str(), &end);
    if (end == s.c_str() || *end != '\0' || !(v > 0.0) || v > 86400.0) {
        throw std::runtime_error(std::string("invalid ") + name + ": " + s +
                                 " (want seconds in (0, 86400])");
    }
    return v;
}

static float parse_audio_gain(const std::string& s)
{
    char* end = nullptr;
    const double v = std::strtod(s.c_str(), &end);
    if (end == s.c_str() || *end != '\0' || !(v >= 0.0) || v > 256.0) {
        throw std::runtime_error("invalid --audio-gain: " + s + " (want float in [0, 256])");
    }
    return static_cast<float>(v);
}

static void parse_ddp(const std::string& spec, Config& cfg)
{
    const auto colon = spec.rfind(':');
    if (colon == std::string::npos) {
        cfg.ddp_host = spec;
        return;
    }
    // IPv6 in [addr]:port is not required for WLED endpoints.
    cfg.ddp_host = spec.substr(0, colon);
    const int port = parse_int_range(spec.substr(colon + 1), "DDP port", 1, 65535);
    cfg.ddp_port = static_cast<uint16_t>(port);
}

Config parse_args(int argc, char** argv)
{
    Config cfg;
    for (int i = 1; i < argc; ++i) {
        const char* a = argv[i];
        if (std::strcmp(a, "--help") == 0 || std::strcmp(a, "-h") == 0) {
            print_usage();
            std::exit(0);
        }
        if (std::strcmp(a, "--width") == 0 || std::strcmp(a, "-W") == 0) {
            cfg.width = parse_dimension(require_value(i, argc, argv, a), "width");
        } else if (starts_with(a, "--width=")) {
            cfg.width = parse_dimension(a + 8, "width");
        } else if (std::strcmp(a, "--height") == 0 || std::strcmp(a, "-H") == 0) {
            cfg.height = parse_dimension(require_value(i, argc, argv, a), "height");
        } else if (starts_with(a, "--height=")) {
            cfg.height = parse_dimension(a + 9, "height");
        } else if (std::strcmp(a, "--fps") == 0) {
            cfg.fps = parse_int_range(require_value(i, argc, argv, a), "fps", 1, 240);
        } else if (starts_with(a, "--fps=")) {
            cfg.fps = parse_int_range(a + 6, "fps", 1, 240);
        } else if (std::strcmp(a, "--ddp") == 0) {
            parse_ddp(require_value(i, argc, argv, a), cfg);
        } else if (starts_with(a, "--ddp=")) {
            parse_ddp(a + 6, cfg);
        } else if (std::strcmp(a, "--preset-path") == 0) {
            cfg.preset_paths.push_back(require_value(i, argc, argv, a));
        } else if (std::strcmp(a, "--texture-path") == 0) {
            cfg.texture_paths.push_back(require_value(i, argc, argv, a));
        } else if (std::strcmp(a, "--preset") == 0) {
            cfg.preset = require_value(i, argc, argv, a);
        } else if (starts_with(a, "--preset=")) {
            cfg.preset = a + 9;
        } else if (std::strcmp(a, "--audio") == 0) {
            cfg.audio = require_value(i, argc, argv, a);
        } else if (starts_with(a, "--audio=")) {
            cfg.audio = a + 8;
        } else if (std::strcmp(a, "--audio-gain") == 0) {
            cfg.audio_gain = parse_audio_gain(require_value(i, argc, argv, a));
        } else if (starts_with(a, "--audio-gain=")) {
            cfg.audio_gain = parse_audio_gain(a + 13);
        } else if (std::strcmp(a, "--sample-rate") == 0) {
            cfg.sample_rate =
                parse_int_range(require_value(i, argc, argv, a), "sample-rate", 8000, 192000);
        } else if (std::strcmp(a, "--frames") == 0) {
            cfg.frames = parse_int_range(require_value(i, argc, argv, a), "frames", 1, 1000000);
        } else if (std::strcmp(a, "--dump-ppm") == 0) {
            cfg.dump_ppm = require_value(i, argc, argv, a);
        } else if (std::strcmp(a, "--software-gl") == 0) {
            cfg.software_gl = true;
        } else if (std::strcmp(a, "--close-on-disconnect") == 0) {
            cfg.close_on_disconnect = true;
        } else if (std::strcmp(a, "--shuffle") == 0) {
            cfg.shuffle = true;
        } else if (std::strcmp(a, "--no-shuffle") == 0) {
            cfg.shuffle = false;
        } else if (std::strcmp(a, "--preset-duration") == 0 ||
                   std::strcmp(a, "--switch-delay") == 0 ||
                   std::strcmp(a, "--shuffle-delay") == 0) {
            // --shuffle-delay remains accepted as a deprecated alias.
            cfg.preset_duration =
                parse_positive_seconds(require_value(i, argc, argv, a), a);
        } else if (starts_with(a, "--preset-duration=")) {
            cfg.preset_duration = parse_positive_seconds(a + 18, "--preset-duration");
        } else if (starts_with(a, "--switch-delay=")) {
            cfg.preset_duration = parse_positive_seconds(a + 15, "--switch-delay");
        } else if (starts_with(a, "--shuffle-delay=")) {
            cfg.preset_duration = parse_positive_seconds(a + 16, "--shuffle-delay");
        } else if (std::strcmp(a, "--quiet") == 0) {
            cfg.quiet = true;
        } else if (std::strcmp(a, "--progress") == 0) {
            cfg.progress = true;
        } else if (std::strcmp(a, "--transition-half-fps") == 0) {
            cfg.transition_half_fps = true;
        } else if (std::strcmp(a, "--no-transition-half-fps") == 0) {
            cfg.transition_half_fps = false;
        } else if (std::strcmp(a, "--warm-presets") == 0) {
            cfg.warm_presets = true;
        } else if (std::strcmp(a, "--no-warm-presets") == 0) {
            cfg.warm_presets = false;
        } else if (std::strcmp(a, "--list-audio") == 0) {
            cfg.list_audio = true;
        } else if (std::strcmp(a, "--set") == 0) {
            const std::string kv = require_value(i, argc, argv, a);
            const auto eq = kv.find('=');
            if (eq == std::string::npos || eq == 0) {
                throw std::runtime_error("--set expects KEY=VALUE");
            }
            cfg.properties.emplace_back(kv.substr(0, eq), kv.substr(eq + 1));
        } else {
            throw std::runtime_error(std::string("unknown argument: ") + a);
        }
    }
    return cfg;
}
