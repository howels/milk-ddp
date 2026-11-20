#include "audio.hpp"

#include <cmath>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <stdexcept>
#include <string>
#include <vector>

#ifdef HAVE_PULSE
#include <pulse/error.h>
#include <pulse/simple.h>
#endif

namespace {

class SineAudio final : public AudioSource {
public:
    explicit SineAudio(int sample_rate) : sample_rate_(sample_rate) {}

    int sample_rate() const override { return sample_rate_; }

    unsigned int fill(std::vector<float>& interleaved, unsigned int frames) override
    {
        interleaved.resize(static_cast<std::size_t>(frames) * 2);
        const double dt = 1.0 / sample_rate_;
        for (unsigned int i = 0; i < frames; ++i) {
            const float s = static_cast<float>(std::sin(phase_ * 2.0 * 3.14159265358979323846));
            interleaved[static_cast<std::size_t>(i) * 2 + 0] = s * 0.7f;
            interleaved[static_cast<std::size_t>(i) * 2 + 1] = s * 0.7f;
            phase_ += 110.0 * dt;
            if (phase_ >= 1.0) {
                phase_ -= 1.0;
            }
        }
        return frames;
    }

private:
    int sample_rate_;
    double phase_ = 0.0;
};

class WavFileAudio final : public AudioSource {
public:
    explicit WavFileAudio(const std::string& path)
    {
        std::ifstream in(path, std::ios::binary);
        if (!in) {
            throw std::runtime_error("cannot open WAV: " + path);
        }
        char riff[12];
        in.read(riff, 12);
        if (!in || std::memcmp(riff, "RIFF", 4) != 0 || std::memcmp(riff + 8, "WAVE", 4) != 0) {
            throw std::runtime_error("not a RIFF/WAVE file: " + path);
        }

        bool got_fmt = false;
        uint16_t audio_format = 0;
        uint16_t channels = 0;
        uint16_t bits = 0;
        uint32_t rate = 0;
        std::vector<char> data;

        while (in) {
            char hdr[8];
            in.read(hdr, 8);
            if (!in) {
                break;
            }
            uint32_t sz = 0;
            std::memcpy(&sz, hdr + 4, 4);
            if (std::memcmp(hdr, "fmt ", 4) == 0) {
                std::vector<char> fmt(sz);
                in.read(fmt.data(), sz);
                if (sz < 16) {
                    throw std::runtime_error("WAV fmt chunk too small");
                }
                std::memcpy(&audio_format, fmt.data() + 0, 2);
                std::memcpy(&channels, fmt.data() + 2, 2);
                std::memcpy(&rate, fmt.data() + 4, 4);
                std::memcpy(&bits, fmt.data() + 14, 2);
                got_fmt = true;
                if (sz & 1) {
                    in.ignore(1);
                }
            } else if (std::memcmp(hdr, "data", 4) == 0) {
                data.resize(sz);
                in.read(data.data(), sz);
                break;
            } else {
                in.seekg(sz + (sz & 1), std::ios::cur);
            }
        }

        if (!got_fmt || data.empty()) {
            throw std::runtime_error("WAV missing fmt or data: " + path);
        }
        if (audio_format != 1 || bits != 16) {
            throw std::runtime_error("WAV must be PCM 16-bit: " + path);
        }
        if (channels != 1 && channels != 2) {
            throw std::runtime_error("WAV must be mono or stereo: " + path);
        }

        sample_rate_ = static_cast<int>(rate);
        channels_ = channels;
        const std::size_t n = data.size() / 2;
        pcm_.resize(n);
        std::memcpy(pcm_.data(), data.data(), n * 2);
    }

    int sample_rate() const override { return sample_rate_; }

    unsigned int fill(std::vector<float>& interleaved, unsigned int frames) override
    {
        interleaved.resize(static_cast<std::size_t>(frames) * 2);
        for (unsigned int i = 0; i < frames; ++i) {
            float l = 0;
            float r = 0;
            if (!pcm_.empty()) {
                if (channels_ == 1) {
                    const float s = pcm_[cursor_] / 32768.0f;
                    l = r = s;
                    cursor_ = (cursor_ + 1) % pcm_.size();
                } else {
                    l = pcm_[cursor_] / 32768.0f;
                    r = pcm_[cursor_ + 1] / 32768.0f;
                    cursor_ = (cursor_ + 2) % pcm_.size();
                }
            }
            interleaved[static_cast<std::size_t>(i) * 2 + 0] = l;
            interleaved[static_cast<std::size_t>(i) * 2 + 1] = r;
        }
        return frames;
    }

private:
    int sample_rate_ = 44100;
    uint16_t channels_ = 2;
    std::vector<int16_t> pcm_;
    std::size_t cursor_ = 0;
};

class StdinAudio final : public AudioSource {
public:
    explicit StdinAudio(int sample_rate) : sample_rate_(sample_rate) {}

    int sample_rate() const override { return sample_rate_; }

    unsigned int fill(std::vector<float>& interleaved, unsigned int frames) override
    {
        std::vector<int16_t> raw(static_cast<std::size_t>(frames) * 2);
        const std::size_t want = raw.size() * sizeof(int16_t);
        std::size_t got = 0;
        while (got < want) {
            const auto n = std::fread(reinterpret_cast<char*>(raw.data()) + got, 1, want - got,
                                      stdin);
            if (n == 0) {
                break;
            }
            got += n;
        }
        const unsigned int have = static_cast<unsigned int>(got / (2 * sizeof(int16_t)));
        interleaved.assign(static_cast<std::size_t>(frames) * 2, 0.0f);
        for (unsigned int i = 0; i < have; ++i) {
            interleaved[static_cast<std::size_t>(i) * 2 + 0] = raw[i * 2] / 32768.0f;
            interleaved[static_cast<std::size_t>(i) * 2 + 1] = raw[i * 2 + 1] / 32768.0f;
        }
        return have == 0 ? frames : have;
    }

private:
    int sample_rate_;
};

#ifdef HAVE_PULSE
class PulseAudio final : public AudioSource {
public:
    explicit PulseAudio(int sample_rate) : sample_rate_(sample_rate)
    {
        pa_sample_spec spec {};
        spec.format = PA_SAMPLE_FLOAT32LE;
        spec.rate = static_cast<uint32_t>(sample_rate_);
        spec.channels = 2;
        int err = 0;
        stream_ = pa_simple_new(nullptr, "milkdrop-ddp", PA_STREAM_RECORD, nullptr,
                                "visualiser", &spec, nullptr, nullptr, &err);
        if (stream_ == nullptr) {
            throw std::runtime_error(std::string("PulseAudio record failed: ") +
                                     pa_strerror(err));
        }
    }

    ~PulseAudio() override
    {
        if (stream_ != nullptr) {
            pa_simple_free(stream_);
        }
    }

    int sample_rate() const override { return sample_rate_; }

    unsigned int fill(std::vector<float>& interleaved, unsigned int frames) override
    {
        interleaved.resize(static_cast<std::size_t>(frames) * 2);
        int err = 0;
        if (pa_simple_read(stream_, interleaved.data(),
                           interleaved.size() * sizeof(float), &err) < 0) {
            throw std::runtime_error(std::string("PulseAudio read failed: ") + pa_strerror(err));
        }
        return frames;
    }

private:
    int sample_rate_;
    pa_simple* stream_ = nullptr;
};
#endif

}  // namespace

std::unique_ptr<AudioSource> make_audio_source(const std::string& spec, int sample_rate)
{
    if (spec == "sine") {
        return std::make_unique<SineAudio>(sample_rate);
    }
    if (spec == "stdin") {
        return std::make_unique<StdinAudio>(sample_rate);
    }
    if (spec.rfind("file:", 0) == 0) {
        return std::make_unique<WavFileAudio>(spec.substr(5));
    }
    if (spec == "pulse") {
#ifdef HAVE_PULSE
        return std::make_unique<PulseAudio>(sample_rate);
#else
        throw std::runtime_error("this build has no PulseAudio support");
#endif
    }
    throw std::runtime_error("unknown --audio spec: " + spec +
                             " (use sine, pulse, file:PATH, or stdin)");
}
