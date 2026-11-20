#pragma once

#include "cli.hpp"

#include <projectM-4/projectM.h>
#include <projectM-4/playlist.h>

void apply_projectm_properties(projectm_handle pm, projectm_playlist_handle playlist,
                               const Config& cfg);
void apply_one_property(projectm_handle pm, projectm_playlist_handle playlist,
                        const std::string& key, const std::string& value);
