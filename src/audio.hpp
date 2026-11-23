/* SPDX-License-Identifier: GPL-3.0-or-later
 * Copyright (C) 2026 milk-ddp contributors
 */
#pragma once

#include <cstdint>
#include <memory>
#include <string>
#include <vector>

class AudioSource {
public:
    virtual ~AudioSource() = default;
    virtual int sample_rate() const = 0;
    // Interleaved stereo float in [-1, 1]. Returns samples per channel.
    virtual unsigned int fill(std::vector<float>& interleaved, unsigned int frames) = 0;
    // While render is paused, call occasionally so capture backends can reconnect
    // a suspended monitor (Pulse/PipeWire) that stopped delivering callbacks.
    virtual void nudge_while_paused() {}
};

// gain: linear amplitude. Pulse applies it as stream soft volume (server-side).
// Other backends scale inside fill() when gain != 1.
std::unique_ptr<AudioSource> make_audio_source(const std::string& spec, int sample_rate,
                                               float gain = 1.0f);

// Print PulseAudio/PipeWire record sources to stdout. Returns 0 on success.
int list_audio_devices();
