/* SPDX-License-Identifier: GPL-3.0-or-later
 * Copyright (C) 2026 milk-ddp contributors
 */
#include "audio.hpp"

#include <algorithm>
#include <atomic>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iostream>
#include <mutex>
#include <stdexcept>
#include <string>
#include <vector>

#ifdef HAVE_PULSE
#include <pulse/pulseaudio.h>
#endif

#ifdef HAVE_ALSA
#include <alsa/asoundlib.h>
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

// Async Pulse capture: subscribe to source/server events so a device that
// appears after start (or replaces the default source) is opened without
// restarting the process. fill() returns silence while disconnected.
class PulseAudio final : public AudioSource {
public:
    // gain is applied as Pulse/PipeWire record-stream soft volume (server-side),
    // not a per-sample multiply in the render thread.
    PulseAudio(int sample_rate, std::string device, float gain)
        : sample_rate_(sample_rate), device_(std::move(device)), gain_(gain)
    {
        // ~1 s of stereo float at the configured rate.
        ring_.assign(static_cast<std::size_t>(sample_rate_) * 2, 0.0f);

        mainloop_ = pa_threaded_mainloop_new();
        if (mainloop_ == nullptr) {
            throw std::runtime_error("PulseAudio: pa_threaded_mainloop_new failed");
        }

        pa_threaded_mainloop_lock(mainloop_);
        context_ = pa_context_new(pa_threaded_mainloop_get_api(mainloop_), "milk-ddp");
        if (context_ == nullptr) {
            pa_threaded_mainloop_unlock(mainloop_);
            pa_threaded_mainloop_free(mainloop_);
            mainloop_ = nullptr;
            throw std::runtime_error("PulseAudio: pa_context_new failed");
        }

        pa_context_set_state_callback(context_, &PulseAudio::on_context_state, this);
        pa_context_set_subscribe_callback(context_, &PulseAudio::on_subscribe, this);

        if (pa_context_connect(context_, nullptr, PA_CONTEXT_NOFLAGS, nullptr) < 0) {
            const char* err = pa_strerror(pa_context_errno(context_));
            pa_context_unref(context_);
            context_ = nullptr;
            pa_threaded_mainloop_unlock(mainloop_);
            pa_threaded_mainloop_free(mainloop_);
            mainloop_ = nullptr;
            throw std::runtime_error(std::string("PulseAudio connect failed: ") + err);
        }
        pa_threaded_mainloop_unlock(mainloop_);

        if (pa_threaded_mainloop_start(mainloop_) < 0) {
            destroy();
            throw std::runtime_error("PulseAudio: mainloop start failed");
        }

        if (!wait_for_context_ready(std::chrono::seconds(5))) {
            destroy();
            throw std::runtime_error("PulseAudio: context did not become ready");
        }

        // Open now if a source exists; otherwise stay silent until hotplug.
        request_open();
    }

    ~PulseAudio() override { destroy(); }

    int sample_rate() const override { return sample_rate_; }

    unsigned int fill(std::vector<float>& interleaved, unsigned int frames) override
    {
        interleaved.assign(static_cast<std::size_t>(frames) * 2, 0.0f);

        // If still offline, periodically nudge an open attempt in case a
        // subscription event was missed (e.g. race at connect time).
        if (!connected_.load(std::memory_order_relaxed)) {
            const auto now = std::chrono::steady_clock::now();
            if (now - last_retry_ >= std::chrono::milliseconds(500)) {
                last_retry_ = now;
                request_open();
            }
            return frames;
        }

        std::lock_guard<std::mutex> lock(ring_mu_);
        const std::size_t want = static_cast<std::size_t>(frames) * 2;
        const std::size_t have = std::min(want, ring_filled_);
        for (std::size_t i = 0; i < have; ++i) {
            interleaved[i] = ring_[ring_read_];
            ring_read_ = (ring_read_ + 1) % ring_.size();
        }
        ring_filled_ -= have;
        return frames;
    }

    void nudge_while_paused() override
    {
        // A monitor that was SUSPENDED at connect (no player yet) can stay
        // READY but deliver no further read callbacks after the sink wakes,
        // until the record stream is reopened. Reconnect if we have not seen
        // PCM for a few seconds while the client is paused.
        if (!connected_.load(std::memory_order_relaxed)) {
            request_open();
            return;
        }
        const auto now = std::chrono::steady_clock::now();
        const auto last_ticks = last_read_ticks_.load(std::memory_order_relaxed);
        if (last_ticks == 0) {
            return;
        }
        const auto last = std::chrono::steady_clock::time_point(
            std::chrono::steady_clock::duration(last_ticks));
        if (now - last < std::chrono::seconds(3)) {
            return;
        }
        if (now - last_nudge_reopen_ < std::chrono::seconds(3)) {
            return;
        }
        last_nudge_reopen_ = now;
        std::cerr << "milk-ddp: PulseAudio capture idle while paused; reopening "
                  << (active_source_.empty() ? "(default)" : active_source_) << "\n";
        // Force reopen even if the stream still reports READY (open_stream_locked
        // would otherwise early-return and leave a stuck capture).
        pa_threaded_mainloop_lock(mainloop_);
        const std::string src = active_source_;
        close_stream_locked();
        if (!src.empty()) {
            open_stream_locked(src.c_str());
        } else if (pa_context_get_state(context_) == PA_CONTEXT_READY) {
            open_after_ready_locked();
        }
        pa_threaded_mainloop_unlock(mainloop_);
    }

private:
    void destroy() noexcept
    {
        if (mainloop_ == nullptr) {
            return;
        }
        pa_threaded_mainloop_stop(mainloop_);
        pa_threaded_mainloop_lock(mainloop_);
        close_stream_locked();
        if (context_ != nullptr) {
            pa_context_disconnect(context_);
            pa_context_unref(context_);
            context_ = nullptr;
        }
        pa_threaded_mainloop_unlock(mainloop_);
        pa_threaded_mainloop_free(mainloop_);
        mainloop_ = nullptr;
        connected_.store(false, std::memory_order_relaxed);
    }

    bool wait_for_context_ready(std::chrono::milliseconds timeout)
    {
        const auto deadline = std::chrono::steady_clock::now() + timeout;
        pa_threaded_mainloop_lock(mainloop_);
        while (pa_context_get_state(context_) != PA_CONTEXT_READY) {
            const auto st = pa_context_get_state(context_);
            if (st == PA_CONTEXT_FAILED || st == PA_CONTEXT_TERMINATED) {
                pa_threaded_mainloop_unlock(mainloop_);
                return false;
            }
            if (std::chrono::steady_clock::now() >= deadline) {
                pa_threaded_mainloop_unlock(mainloop_);
                return false;
            }
            pa_threaded_mainloop_wait(mainloop_);
        }
        pa_threaded_mainloop_unlock(mainloop_);
        return true;
    }

    void request_open()
    {
        if (mainloop_ == nullptr || context_ == nullptr) {
            return;
        }
        pa_threaded_mainloop_lock(mainloop_);
        if (pa_context_get_state(context_) != PA_CONTEXT_READY) {
            pa_threaded_mainloop_unlock(mainloop_);
            return;
        }
        if (!device_.empty()) {
            open_stream_locked(device_.c_str());
        } else {
            // Resolve the current default source, then open it.
            pa_operation* op =
                pa_context_get_server_info(context_, &PulseAudio::on_server_info, this);
            if (op != nullptr) {
                pa_operation_unref(op);
            }
        }
        pa_threaded_mainloop_unlock(mainloop_);
    }

    void close_stream_locked()
    {
        if (stream_ != nullptr) {
            pa_stream_set_state_callback(stream_, nullptr, nullptr);
            pa_stream_set_read_callback(stream_, nullptr, nullptr);
            if (pa_stream_get_state(stream_) != PA_STREAM_UNCONNECTED) {
                pa_stream_disconnect(stream_);
            }
            pa_stream_unref(stream_);
            stream_ = nullptr;
        }
        connected_.store(false, std::memory_order_relaxed);
        {
            std::lock_guard<std::mutex> lock(ring_mu_);
            ring_read_ = ring_write_ = 0;
            ring_filled_ = 0;
        }
    }

    void open_stream_locked(const char* source)
    {
        if (source == nullptr || source[0] == '\0') {
            return;
        }
        if (stream_ != nullptr && active_source_ == source &&
            pa_stream_get_state(stream_) == PA_STREAM_READY) {
            return;
        }

        close_stream_locked();
        active_source_ = source;

        pa_sample_spec spec {};
        spec.format = PA_SAMPLE_FLOAT32LE;
        spec.rate = static_cast<uint32_t>(sample_rate_);
        spec.channels = 2;

        pa_buffer_attr attr {};
        attr.maxlength = static_cast<uint32_t>(-1);
        attr.tlength = static_cast<uint32_t>(-1);
        attr.prebuf = static_cast<uint32_t>(-1);
        attr.minreq = static_cast<uint32_t>(-1);
        // ~50 ms fragments keep latency low for the visualiser.
        attr.fragsize = static_cast<uint32_t>(sample_rate_ / 20 * 2 * sizeof(float));

        stream_ = pa_stream_new(context_, "visualiser", &spec, nullptr);
        if (stream_ == nullptr) {
            std::cerr << "milk-ddp: PulseAudio stream create failed: "
                      << pa_strerror(pa_context_errno(context_)) << "\n";
            return;
        }

        pa_stream_set_state_callback(stream_, &PulseAudio::on_stream_state, this);
        pa_stream_set_read_callback(stream_, &PulseAudio::on_stream_read, this);

        const pa_stream_flags_t flags = static_cast<pa_stream_flags_t>(
            PA_STREAM_ADJUST_LATENCY | PA_STREAM_AUTO_TIMING_UPDATE);

        if (pa_stream_connect_record(stream_, source, &attr, flags) < 0) {
            std::cerr << "milk-ddp: PulseAudio connect_record(" << source
                      << ") failed: " << pa_strerror(pa_context_errno(context_)) << "\n";
            close_stream_locked();
            active_source_.clear();
        }
    }

    static void on_context_state(pa_context* ctx, void* userdata)
    {
        auto* self = static_cast<PulseAudio*>(userdata);
        switch (pa_context_get_state(ctx)) {
        case PA_CONTEXT_READY: {
            pa_operation* sub = pa_context_subscribe(
                ctx,
                static_cast<pa_subscription_mask_t>(PA_SUBSCRIPTION_MASK_SOURCE |
                                                    PA_SUBSCRIPTION_MASK_SERVER),
                nullptr, nullptr);
            if (sub != nullptr) {
                pa_operation_unref(sub);
            }
            self->open_after_ready_locked();
            pa_threaded_mainloop_signal(self->mainloop_, 0);
            break;
        }
        case PA_CONTEXT_FAILED:
        case PA_CONTEXT_TERMINATED:
            self->close_stream_locked();
            pa_threaded_mainloop_signal(self->mainloop_, 0);
            break;
        default:
            pa_threaded_mainloop_signal(self->mainloop_, 0);
            break;
        }
    }

    void open_after_ready_locked()
    {
        if (!device_.empty()) {
            open_stream_locked(device_.c_str());
        } else {
            pa_operation* op =
                pa_context_get_server_info(context_, &PulseAudio::on_server_info, this);
            if (op != nullptr) {
                pa_operation_unref(op);
            }
        }
    }

    static void on_server_info(pa_context* /*ctx*/, const pa_server_info* info, void* userdata)
    {
        auto* self = static_cast<PulseAudio*>(userdata);
        if (info == nullptr || info->default_source_name == nullptr) {
            return;
        }
        self->open_stream_locked(info->default_source_name);
    }

    static void on_subscribe(pa_context* ctx, pa_subscription_event_type_t type, uint32_t /*idx*/,
                             void* userdata)
    {
        auto* self = static_cast<PulseAudio*>(userdata);
        const auto facility = static_cast<pa_subscription_event_type_t>(
            type & PA_SUBSCRIPTION_EVENT_FACILITY_MASK);
        const auto event = static_cast<pa_subscription_event_type_t>(
            type & PA_SUBSCRIPTION_EVENT_TYPE_MASK);

        if (facility == PA_SUBSCRIPTION_EVENT_SERVER &&
            (event == PA_SUBSCRIPTION_EVENT_CHANGE || event == PA_SUBSCRIPTION_EVENT_NEW)) {
            // Default source may have changed.
            if (self->device_.empty()) {
                pa_operation* op =
                    pa_context_get_server_info(ctx, &PulseAudio::on_server_info, self);
                if (op != nullptr) {
                    pa_operation_unref(op);
                }
            }
            return;
        }

        if (facility == PA_SUBSCRIPTION_EVENT_SOURCE) {
            if (event == PA_SUBSCRIPTION_EVENT_NEW || event == PA_SUBSCRIPTION_EVENT_CHANGE) {
                if (!self->device_.empty()) {
                    self->open_stream_locked(self->device_.c_str());
                } else {
                    pa_operation* op =
                        pa_context_get_server_info(ctx, &PulseAudio::on_server_info, self);
                    if (op != nullptr) {
                        pa_operation_unref(op);
                    }
                }
            } else if (event == PA_SUBSCRIPTION_EVENT_REMOVE) {
                // Stream state callback will mark us disconnected; retry via
                // server info so a remaining default source is picked up.
                if (self->device_.empty()) {
                    pa_operation* op =
                        pa_context_get_server_info(ctx, &PulseAudio::on_server_info, self);
                    if (op != nullptr) {
                        pa_operation_unref(op);
                    }
                } else {
                    self->close_stream_locked();
                }
            }
        }
    }

    void apply_stream_volume_locked()
    {
        if (stream_ == nullptr || gain_ == 1.0f) {
            return;
        }
        const uint32_t idx = pa_stream_get_index(stream_);
        if (idx == PA_INVALID_INDEX) {
            return;
        }
        // Soft volume on the source-output (record stream). Linear amplitude may
        // exceed 0 dBFS; PipeWire/Pulse apply it in the mixing graph.
        pa_cvolume vol;
        const pa_volume_t v = pa_sw_volume_from_linear(static_cast<double>(gain_));
        const uint8_t ch = pa_stream_get_sample_spec(stream_)->channels;
        pa_cvolume_set(&vol, ch, v);
        pa_operation* op =
            pa_context_set_source_output_volume(context_, idx, &vol, nullptr, nullptr);
        if (op != nullptr) {
            pa_operation_unref(op);
        } else {
            std::cerr << "milk-ddp: PulseAudio set_source_output_volume failed: "
                      << pa_strerror(pa_context_errno(context_)) << "\n";
        }
    }

    static void on_stream_state(pa_stream* stream, void* userdata)
    {
        auto* self = static_cast<PulseAudio*>(userdata);
        switch (pa_stream_get_state(stream)) {
        case PA_STREAM_READY:
            self->connected_.store(true, std::memory_order_relaxed);
            self->apply_stream_volume_locked();
            std::cerr << "milk-ddp: PulseAudio recording from "
                      << (self->active_source_.empty() ? "(default)" : self->active_source_)
                      << "  soft-volume gain=" << self->gain_ << "\n";
            break;
        case PA_STREAM_FAILED:
            std::cerr << "milk-ddp: PulseAudio stream failed: "
                      << pa_strerror(pa_context_errno(self->context_)) << "\n";
            self->connected_.store(false, std::memory_order_relaxed);
            break;
        case PA_STREAM_TERMINATED:
            self->connected_.store(false, std::memory_order_relaxed);
            break;
        default:
            break;
        }
    }

    static void on_stream_read(pa_stream* stream, size_t /*nbytes*/, void* userdata)
    {
        auto* self = static_cast<PulseAudio*>(userdata);
        const void* data = nullptr;
        size_t bytes = 0;
        if (pa_stream_peek(stream, &data, &bytes) < 0) {
            return;
        }
        if (data == nullptr && bytes > 0) {
            // Hole in the buffer; drop it.
            pa_stream_drop(stream);
            return;
        }
        if (data == nullptr || bytes == 0) {
            if (bytes == 0) {
                pa_stream_drop(stream);
            }
            return;
        }

        const auto* samples = static_cast<const float*>(data);
        const std::size_t count = bytes / sizeof(float);
        {
            std::lock_guard<std::mutex> lock(self->ring_mu_);
            for (std::size_t i = 0; i < count; ++i) {
                self->ring_[self->ring_write_] = samples[i];
                self->ring_write_ = (self->ring_write_ + 1) % self->ring_.size();
                if (self->ring_filled_ < self->ring_.size()) {
                    ++self->ring_filled_;
                } else {
                    self->ring_read_ = (self->ring_read_ + 1) % self->ring_.size();
                }
            }
        }
        self->last_read_ticks_.store(
            std::chrono::steady_clock::now().time_since_epoch().count(),
            std::memory_order_relaxed);
        pa_stream_drop(stream);
    }

    int sample_rate_;
    std::string device_;
    std::string active_source_;
    float gain_ = 1.0f;

    pa_threaded_mainloop* mainloop_ = nullptr;
    pa_context* context_ = nullptr;
    pa_stream* stream_ = nullptr;

    std::vector<float> ring_;
    std::size_t ring_read_ = 0;
    std::size_t ring_write_ = 0;
    std::size_t ring_filled_ = 0;
    std::mutex ring_mu_;
    std::atomic<bool> connected_{false};
    std::atomic<std::chrono::steady_clock::rep> last_read_ticks_{0};
    std::chrono::steady_clock::time_point last_retry_{};
    std::chrono::steady_clock::time_point last_nudge_reopen_{};
};

#endif  // HAVE_PULSE

#ifdef HAVE_ALSA

// ALSA capture with reconnect: if the device is missing at start or is
// unplugged later, fill() returns silence and retries open every 500 ms.
class AlsaAudio final : public AudioSource {
public:
    AlsaAudio(int sample_rate, std::string device)
        : sample_rate_(sample_rate), device_(device.empty() ? "default" : std::move(device))
    {
        if (!try_open()) {
            std::cerr << "milk-ddp: ALSA device \"" << device_
                      << "\" not open yet; will retry when it appears\n";
        }
    }

    ~AlsaAudio() override { close(); }

    int sample_rate() const override { return sample_rate_; }

    unsigned int fill(std::vector<float>& interleaved, unsigned int frames) override
    {
        interleaved.assign(static_cast<std::size_t>(frames) * 2, 0.0f);

        if (pcm_ == nullptr) {
            const auto now = std::chrono::steady_clock::now();
            if (now - last_retry_ >= std::chrono::milliseconds(500)) {
                last_retry_ = now;
                try_open();
            }
            return frames;
        }

        const snd_pcm_sframes_t want = static_cast<snd_pcm_sframes_t>(frames);
        const snd_pcm_sframes_t got = snd_pcm_readi(pcm_, interleaved.data(), want);
        if (got == -EPIPE || got == -ESTRPIPE) {
            snd_pcm_prepare(pcm_);
            return frames;
        }
        if (got < 0) {
            std::cerr << "milk-ddp: ALSA read failed: " << snd_strerror(static_cast<int>(got))
                      << "\n";
            close();
            return frames;
        }
        if (got < want) {
            // Partial read already wrote the leading samples; leave the rest zero.
        }
        return frames;
    }

private:
    bool try_open()
    {
        close();
        int err = snd_pcm_open(&pcm_, device_.c_str(), SND_PCM_STREAM_CAPTURE, 0);
        if (err < 0) {
            pcm_ = nullptr;
            return false;
        }

        // soft_resample=1 lets plughw/default convert rate/channels when needed.
        err = snd_pcm_set_params(pcm_, SND_PCM_FORMAT_FLOAT_LE, SND_PCM_ACCESS_RW_INTERLEAVED, 2,
                                 static_cast<unsigned int>(sample_rate_), 1, 500000);
        if (err < 0) {
            std::cerr << "milk-ddp: ALSA set_params(" << device_
                      << ") failed: " << snd_strerror(err) << "\n";
            close();
            return false;
        }

        err = snd_pcm_prepare(pcm_);
        if (err < 0) {
            std::cerr << "milk-ddp: ALSA prepare(" << device_
                      << ") failed: " << snd_strerror(err) << "\n";
            close();
            return false;
        }

        std::cerr << "milk-ddp: ALSA recording from " << device_ << "\n";
        return true;
    }

    void close() noexcept
    {
        if (pcm_ != nullptr) {
            snd_pcm_close(pcm_);
            pcm_ = nullptr;
        }
    }

    int sample_rate_;
    std::string device_;
    snd_pcm_t* pcm_ = nullptr;
    std::chrono::steady_clock::time_point last_retry_{};
};

#endif  // HAVE_ALSA

}  // namespace

namespace {

#ifdef HAVE_PULSE
int list_pulse_sources()
{
    struct SourceRow {
        std::string name;
        std::string description;
        bool monitor = false;
    };

    struct ListState {
        std::string default_source;
        std::vector<SourceRow> sources;
        bool failed = false;
        bool got_server = false;
        bool got_sources = false;
    } state;

    pa_mainloop* mainloop = pa_mainloop_new();
    if (mainloop == nullptr) {
        std::cout << "PulseAudio/PipeWire: mainloop create failed\n";
        return 1;
    }

    pa_context* context = pa_context_new(pa_mainloop_get_api(mainloop), "milk-ddp-list");
    if (context == nullptr) {
        pa_mainloop_free(mainloop);
        std::cout << "PulseAudio/PipeWire: context create failed\n";
        return 1;
    }

    pa_context_set_state_callback(
        context,
        [](pa_context* ctx, void* userdata) {
            auto* st = static_cast<ListState*>(userdata);
            switch (pa_context_get_state(ctx)) {
            case PA_CONTEXT_READY: {
                pa_operation* server_op = pa_context_get_server_info(
                    ctx,
                    [](pa_context* /*c*/, const pa_server_info* info, void* ud) {
                        auto* s = static_cast<ListState*>(ud);
                        if (info != nullptr && info->default_source_name != nullptr) {
                            s->default_source = info->default_source_name;
                        }
                        s->got_server = true;
                    },
                    st);
                if (server_op != nullptr) {
                    pa_operation_unref(server_op);
                } else {
                    st->got_server = true;
                }

                pa_operation* list_op = pa_context_get_source_info_list(
                    ctx,
                    [](pa_context* /*c*/, const pa_source_info* info, int eol, void* ud) {
                        auto* s = static_cast<ListState*>(ud);
                        if (eol) {
                            s->got_sources = true;
                            return;
                        }
                        if (info == nullptr || info->name == nullptr) {
                            return;
                        }
                        SourceRow row;
                        row.name = info->name;
                        if (info->description != nullptr) {
                            row.description = info->description;
                        }
                        row.monitor = info->monitor_of_sink != PA_INVALID_INDEX;
                        s->sources.push_back(std::move(row));
                    },
                    st);
                if (list_op != nullptr) {
                    pa_operation_unref(list_op);
                } else {
                    st->failed = true;
                    st->got_sources = true;
                }
                break;
            }
            case PA_CONTEXT_FAILED:
            case PA_CONTEXT_TERMINATED:
                st->failed = true;
                st->got_server = true;
                st->got_sources = true;
                break;
            default:
                break;
            }
        },
        &state);

    if (pa_context_connect(context, nullptr, PA_CONTEXT_NOFLAGS, nullptr) < 0) {
        std::cout << "PulseAudio/PipeWire: connect failed ("
                  << pa_strerror(pa_context_errno(context))
                  << "). Is the daemon running?\n";
        pa_context_unref(context);
        pa_mainloop_free(mainloop);
        return 1;
    }

    const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(5);
    while (!(state.got_server && state.got_sources)) {
        if (std::chrono::steady_clock::now() >= deadline) {
            state.failed = true;
            break;
        }
        if (pa_mainloop_iterate(mainloop, 1, nullptr) < 0) {
            state.failed = true;
            break;
        }
    }

    pa_context_disconnect(context);
    pa_context_unref(context);
    pa_mainloop_free(mainloop);

    std::cout << "PulseAudio/PipeWire record sources\n"
              << "(--audio pulse | --audio pulse:NAME)\n\n";
    if (state.failed && state.sources.empty()) {
        std::cout << "  (unavailable)\n\n";
        return 1;
    }
    if (!state.default_source.empty()) {
        std::cout << "default: " << state.default_source << "\n\n";
    }
    if (state.sources.empty()) {
        std::cout << "  (no record sources)\n\n";
        return 0;
    }
    for (const auto& src : state.sources) {
        const bool is_default = !state.default_source.empty() && src.name == state.default_source;
        std::cout << (is_default ? "* " : "  ") << src.name;
        if (!src.description.empty()) {
            std::cout << "\n    " << src.description;
        }
        if (src.monitor) {
            std::cout << "  [monitor]";
        }
        if (is_default) {
            std::cout << "  [default]";
        }
        std::cout << "\n";
    }
    std::cout << "\n";
    return 0;
}
#endif

#ifdef HAVE_ALSA
int list_alsa_devices()
{
    std::cout << "ALSA capture devices\n"
              << "(--audio alsa | --audio alsa:DEVICE)\n\n";
    std::cout << "* default\n    ALSA default capture PCM\n";

    void** hints = nullptr;
    if (snd_device_name_hint(-1, "pcm", &hints) < 0 || hints == nullptr) {
        std::cout << "  (snd_device_name_hint failed)\n\n";
        return 1;
    }

    int count = 1;  // default
    for (void** h = hints; *h != nullptr; ++h) {
        char* name = snd_device_name_get_hint(*h, "NAME");
        char* desc = snd_device_name_get_hint(*h, "DESC");
        char* ioid = snd_device_name_get_hint(*h, "IOID");

        // NULL IOID means bidirectional; skip pure Output devices.
        const bool input_ok = (ioid == nullptr) || (std::strcmp(ioid, "Input") == 0);
        if (name != nullptr && input_ok && std::strcmp(name, "default") != 0 &&
            std::strcmp(name, "null") != 0) {
            std::cout << "  " << name;
            if (desc != nullptr && desc[0] != '\0') {
                // DESC may contain newlines; print first line only for compactness.
                std::string d(desc);
                const auto nl = d.find('\n');
                if (nl != std::string::npos) {
                    d.resize(nl);
                }
                std::cout << "\n    " << d;
            }
            std::cout << "\n";
            ++count;
        }

        free(name);
        free(desc);
        free(ioid);
    }
    snd_device_name_free_hint(hints);

    std::cout << "\n" << count << " ALSA device(s). Prefer plughw:… when the card "
              << "needs rate conversion.\n\n";
    return 0;
}
#endif

// Software gain for non-Pulse backends (one pass inside fill, not the GL thread
// beyond what fill already does). Pulse uses server soft volume instead.
class GainAudio final : public AudioSource {
public:
    GainAudio(std::unique_ptr<AudioSource> inner, float gain)
        : inner_(std::move(inner)), gain_(gain)
    {
    }

    int sample_rate() const override { return inner_->sample_rate(); }

    unsigned int fill(std::vector<float>& interleaved, unsigned int frames) override
    {
        const unsigned int got = inner_->fill(interleaved, frames);
        if (gain_ != 1.0f && !interleaved.empty()) {
            for (float& s : interleaved) {
                s *= gain_;
                if (s > 1.0f) {
                    s = 1.0f;
                } else if (s < -1.0f) {
                    s = -1.0f;
                }
            }
        }
        return got;
    }

    void nudge_while_paused() override { inner_->nudge_while_paused(); }

private:
    std::unique_ptr<AudioSource> inner_;
    float gain_;
};

}  // namespace

std::unique_ptr<AudioSource> make_audio_source(const std::string& spec, int sample_rate,
                                               float gain)
{
    std::unique_ptr<AudioSource> src;
    if (spec == "sine") {
        src = std::make_unique<SineAudio>(sample_rate);
    } else if (spec == "stdin") {
        src = std::make_unique<StdinAudio>(sample_rate);
    } else if (spec.rfind("file:", 0) == 0) {
        src = std::make_unique<WavFileAudio>(spec.substr(5));
    } else if (spec == "pulse" || spec.rfind("pulse:", 0) == 0) {
#ifdef HAVE_PULSE
        std::string device;
        if (spec.rfind("pulse:", 0) == 0) {
            device = spec.substr(6);
        }
        // Soft volume is set on the record stream; do not wrap with GainAudio.
        return std::make_unique<PulseAudio>(sample_rate, std::move(device), gain);
#else
        throw std::runtime_error("this build has no PulseAudio support");
#endif
    } else if (spec == "alsa" || spec.rfind("alsa:", 0) == 0) {
#ifdef HAVE_ALSA
        std::string device;
        if (spec.rfind("alsa:", 0) == 0) {
            device = spec.substr(5);
        }
        src = std::make_unique<AlsaAudio>(sample_rate, std::move(device));
#else
        throw std::runtime_error("this build has no ALSA support");
#endif
    } else {
        throw std::runtime_error(
            "unknown --audio spec: " + spec +
            " (use sine, pulse, pulse:SOURCE, alsa, alsa:DEVICE, file:PATH, or stdin)");
    }
    if (gain != 1.0f) {
        src = std::make_unique<GainAudio>(std::move(src), gain);
    }
    return src;
}

int list_audio_devices()
{
    std::cout << "Built-in\n"
              << "  sine                 generated test tone\n"
              << "  file:PATH            loop a 16-bit PCM WAV\n"
              << "  stdin                raw stereo s16le at --sample-rate\n\n";

    int rc = 0;
#ifdef HAVE_PULSE
    if (list_pulse_sources() != 0) {
        rc = 1;
    }
#else
    std::cout << "PulseAudio/PipeWire: not compiled in (install libpulse-dev and rebuild)\n\n";
#endif

#ifdef HAVE_ALSA
    if (list_alsa_devices() != 0) {
        rc = 1;
    }
#else
    std::cout << "ALSA: not compiled in (install libasound2-dev and rebuild)\n\n";
#endif

    std::cout << "Examples:\n"
              << "  milk-ddp --audio pulse …\n"
              << "  milk-ddp --audio pulse:SOURCE …\n"
              << "  milk-ddp --audio alsa …\n"
              << "  milk-ddp --audio alsa:plughw:1,0 …\n";
    return rc;
}
