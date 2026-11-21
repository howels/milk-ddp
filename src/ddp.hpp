#pragma once

#include <chrono>
#include <cstdint>
#include <string>
#include <vector>

class DdpSender {
public:
    /** When close_on_disconnect is false (default), send() failures are logged
     *  and the frame is dropped; the process keeps rendering. When true, the
     *  first send() failure throws (previous milk-ddp behaviour). */
    DdpSender(const std::string& host, uint16_t port, bool close_on_disconnect = false);
    ~DdpSender();

    DdpSender(const DdpSender&) = delete;
    DdpSender& operator=(const DdpSender&) = delete;

    void send_rgb_frame(const unsigned char* rgb, std::size_t pixel_count);

    /** Numeric peer used after resolve (IPv4 preferred). */
    const std::string& peer() const { return peer_; }

private:
    int fd_ = -1;
    uint8_t sequence_ = 1;
    bool close_on_disconnect_ = false;
    std::string peer_;
    std::vector<unsigned char> packet_;
    // Rate-limit stderr when the peer is down (avoid one line per frame).
    std::chrono::steady_clock::time_point next_send_error_log_{};
};
