/* SPDX-License-Identifier: GPL-3.0-or-later
 * Copyright (C) 2026 milk-ddp contributors
 */
#pragma once

#include "cli.hpp"

#include <projectM-4/projectM.h>
#include <projectM-4/playlist.h>

void apply_projectm_properties(projectm_handle pm, projectm_playlist_handle playlist,
                               const Config& cfg);
void apply_one_property(projectm_handle pm, projectm_playlist_handle playlist,
                        const std::string& key, const std::string& value);
