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
};

std::unique_ptr<AudioSource> make_audio_source(const std::string& spec, int sample_rate);

// Print PulseAudio/PipeWire record sources to stdout. Returns 0 on success.
int list_audio_devices();
