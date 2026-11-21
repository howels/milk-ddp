#pragma once

#include <cstdint>
#include <string>
#include <utility>
#include <vector>

struct Config {
    int width = 128;
    int height = 128;
    int fps = 30;
    std::string ddp_host = "127.0.0.1";
    uint16_t ddp_port = 4048;
    std::vector<std::string> preset_paths;
    std::vector<std::string> texture_paths;
    std::string preset;  // file, idle://, or empty (playlist)
    std::string audio = "sine";
    // Linear amplitude. Pulse/PipeWire: record-stream soft volume (no per-sample
    // loop). Other backends: scale inside fill(). Quiet monitors: try 1.5–4.0.
    float audio_gain = 1.0f;
    int sample_rate = 44100;
    int frames = 0;  // 0 = run until signal
    std::string dump_ppm;
    bool software_gl = false;
    // Default: log DDP send errors and keep rendering (container-friendly).
    // --close-on-disconnect restores exit-on-send-failure.
    bool close_on_disconnect = false;
    bool shuffle = false;
    // Seconds each playlist preset is shown before the next soft/hard cut.
    // Negative means leave libprojectM's default (30 s).
    double preset_duration = -1.0;
    bool quiet = false;      // suppress startup banner, preset lines, and progress
    bool progress = false;   // periodic status line with measured fps on stderr
    bool list_audio = false; // print Pulse/ALSA devices and exit
    // Soft cuts render both presets (~2× GPU). When true, pace at fps/2 for
    // soft_cut_duration and feed 2× PCM so wall-clock audio stays correct.
    // Off by default; enable with --transition-half-fps.
    bool transition_half_fps = false;
    // Hard-cut through the playlist at startup (1 frame each, no DDP) so Mesa
    // can populate its on-disk GLSL cache before normal play. On by default for
    // playlist mode; disable with --no-warm-presets.
    bool warm_presets = true;
    std::vector<std::pair<std::string, std::string>> properties;
};

void print_usage();
Config parse_args(int argc, char** argv);
