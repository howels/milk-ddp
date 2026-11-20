#include "projectm_props.hpp"

#include <cctype>
#include <stdexcept>
#include <string>

namespace {

std::string lower(std::string s)
{
    for (char& c : s) {
        c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
    }
    return s;
}

bool parse_bool(const std::string& v)
{
    const std::string s = lower(v);
    if (s == "1" || s == "true" || s == "yes" || s == "on") {
        return true;
    }
    if (s == "0" || s == "false" || s == "no" || s == "off") {
        return false;
    }
    throw std::runtime_error("not a boolean: " + v);
}

double parse_double(const std::string& v)
{
    char* end = nullptr;
    const double d = std::strtod(v.c_str(), &end);
    if (end == v.c_str() || *end != '\0') {
        throw std::runtime_error("not a number: " + v);
    }
    return d;
}

}  // namespace

void apply_one_property(projectm_handle pm, projectm_playlist_handle playlist,
                        const std::string& key, const std::string& value)
{
    const std::string k = lower(key);
    if (k == "beat_sensitivity") {
        projectm_set_beat_sensitivity(pm, static_cast<float>(parse_double(value)));
    } else if (k == "hard_cut_duration") {
        projectm_set_hard_cut_duration(pm, parse_double(value));
    } else if (k == "hard_cut_enabled") {
        projectm_set_hard_cut_enabled(pm, parse_bool(value));
    } else if (k == "hard_cut_sensitivity") {
        projectm_set_hard_cut_sensitivity(pm, static_cast<float>(parse_double(value)));
    } else if (k == "soft_cut_duration") {
        projectm_set_soft_cut_duration(pm, parse_double(value));
    } else if (k == "preset_duration" || k == "displayduration" || k == "display_duration") {
        projectm_set_preset_duration(pm, parse_double(value));
    } else if (k == "mesh_size") {
        const auto x = value.find('x');
        const auto X = value.find('X');
        const auto sep = x != std::string::npos ? x : X;
        if (sep == std::string::npos) {
            throw std::runtime_error("mesh_size expects WxH");
        }
        const std::size_t w = static_cast<std::size_t>(parse_double(value.substr(0, sep)));
        const std::size_t h = static_cast<std::size_t>(parse_double(value.substr(sep + 1)));
        projectm_set_mesh_size(pm, w, h);
    } else if (k == "aspect_correction") {
        projectm_set_aspect_correction(pm, parse_bool(value));
    } else if (k == "easter_egg") {
        projectm_set_easter_egg(pm, static_cast<float>(parse_double(value)));
    } else if (k == "preset_locked") {
        projectm_set_preset_locked(pm, parse_bool(value));
    } else if (k == "shuffle") {
        if (playlist != nullptr) {
            projectm_playlist_set_shuffle(playlist, parse_bool(value));
        }
    } else {
        throw std::runtime_error("unknown projectM property: " + key);
    }
}

void apply_projectm_properties(projectm_handle pm, projectm_playlist_handle playlist,
                               const Config& cfg)
{
    projectm_set_window_size(pm, static_cast<std::size_t>(cfg.width),
                             static_cast<std::size_t>(cfg.height));
    projectm_set_fps(pm, cfg.fps);
    if (cfg.preset_duration > 0.0) {
        projectm_set_preset_duration(pm, cfg.preset_duration);
    }
    if (playlist != nullptr) {
        projectm_playlist_set_shuffle(playlist, cfg.shuffle);
    }
    // --set can override --preset-duration / --shuffle-delay.
    for (const auto& kv : cfg.properties) {
        apply_one_property(pm, playlist, kv.first, kv.second);
    }
}
