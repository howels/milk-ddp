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
    int sample_rate = 44100;
    int frames = 0;  // 0 = run until signal
    std::string dump_ppm;
    bool software_gl = false;
    bool shuffle = false;
    // Seconds each playlist preset is shown before the next soft/hard cut.
    // Negative means leave libprojectM's default (30 s).
    double preset_duration = -1.0;
    bool quiet = false;      // suppress startup banner, preset lines, and progress
    bool progress = false;   // periodic status line with measured fps on stderr
    bool list_audio = false; // print Pulse/ALSA devices and exit
    std::vector<std::pair<std::string, std::string>> properties;
};

void print_usage();
Config parse_args(int argc, char** argv);
