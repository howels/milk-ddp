#include "ddp.hpp"

#include <arpa/inet.h>
#include <netdb.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>

#include <algorithm>
#include <cerrno>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <string>

namespace {
constexpr std::size_t kHeader = 10;
constexpr std::size_t kMaxRgbBytes = 1440;  // WLED DDP_CHANNELS_PER_PACKET
constexpr uint8_t kVer1 = 0x40;
constexpr uint8_t kPush = 0x01;
constexpr uint8_t kRgb24 = 0x0B;
constexpr uint8_t kDestDisplay = 1;

std::string format_peer(const sockaddr* addr, socklen_t len)
{
    char host[INET6_ADDRSTRLEN] = {};
    char serv[16] = {};
    const int rc = getnameinfo(addr, len, host, sizeof(host), serv, sizeof(serv),
                               NI_NUMERICHOST | NI_NUMERICSERV);
    if (rc != 0) {
        return std::string("unknown (") + gai_strerror(rc) + ")";
    }
    if (addr->sa_family == AF_INET6) {
        return std::string("[") + host + "]:" + serv;
    }
    return std::string(host) + ":" + serv;
}

// WLED on ESP32 listens on IPv4 UDP only. Dual-stack DNS often returns AAAA
// first; a connected UDP socket to that AAAA "succeeds" while packets never
// reach the controller. Prefer AF_INET, then fall back to AF_INET6.
int connect_udp(const std::string& host, uint16_t port, std::string& peer_out)
{
    const int families[] = {AF_INET, AF_INET6};
    std::string last_error = "no addresses";

    for (int family : families) {
        addrinfo hints {};
        hints.ai_family = family;
        hints.ai_socktype = SOCK_DGRAM;

        addrinfo* result = nullptr;
        const int rc =
            getaddrinfo(host.c_str(), std::to_string(port).c_str(), &hints, &result);
        if (rc != 0) {
            last_error = gai_strerror(rc);
            continue;
        }

        int fd = -1;
        for (addrinfo* ai = result; ai != nullptr; ai = ai->ai_next) {
            fd = ::socket(ai->ai_family, ai->ai_socktype, ai->ai_protocol);
            if (fd < 0) {
                last_error = std::strerror(errno);
                continue;
            }
            if (::connect(fd, ai->ai_addr, ai->ai_addrlen) == 0) {
                peer_out = format_peer(ai->ai_addr, ai->ai_addrlen);
                freeaddrinfo(result);
                return fd;
            }
            last_error = std::strerror(errno);
            ::close(fd);
            fd = -1;
        }
        freeaddrinfo(result);
    }

    throw std::runtime_error("DDP UDP connect failed for " + host + ":" +
                             std::to_string(port) + " (" + last_error + ")");
}
}  // namespace

DdpSender::DdpSender(const std::string& host, uint16_t port, bool close_on_disconnect)
    : close_on_disconnect_(close_on_disconnect)
{
    fd_ = connect_udp(host, port, peer_);
    packet_.reserve(kHeader + kMaxRgbBytes);
}

DdpSender::~DdpSender()
{
    if (fd_ >= 0) {
        ::close(fd_);
    }
}

void DdpSender::send_rgb_frame(const unsigned char* rgb, std::size_t pixel_count)
{
    const std::size_t total = pixel_count * 3;
    std::size_t offset = 0;
    const uint8_t seq = sequence_;
    sequence_ = static_cast<uint8_t>(sequence_ == 15 ? 1 : sequence_ + 1);

    while (offset < total) {
        const std::size_t chunk = std::min(kMaxRgbBytes, total - offset);
        const bool last = (offset + chunk) >= total;

        packet_.resize(kHeader + chunk);
        packet_[0] = static_cast<unsigned char>(kVer1 | (last ? kPush : 0));
        packet_[1] = seq;
        packet_[2] = kRgb24;
        packet_[3] = kDestDisplay;
        packet_[4] = static_cast<unsigned char>((offset >> 24) & 0xFF);
        packet_[5] = static_cast<unsigned char>((offset >> 16) & 0xFF);
        packet_[6] = static_cast<unsigned char>((offset >> 8) & 0xFF);
        packet_[7] = static_cast<unsigned char>(offset & 0xFF);
        packet_[8] = static_cast<unsigned char>((chunk >> 8) & 0xFF);
        packet_[9] = static_cast<unsigned char>(chunk & 0xFF);
        std::memcpy(packet_.data() + kHeader, rgb + offset, chunk);

        const ssize_t n = ::send(fd_, packet_.data(), packet_.size(), 0);
        if (n < 0 || static_cast<std::size_t>(n) != packet_.size()) {
            const int err = errno;
            const char* detail = (n < 0) ? std::strerror(err) : "short write";
            const std::string msg =
                std::string("DDP endpoint offline (") + peer_ + ": " + detail + ")";
            if (close_on_disconnect_) {
                throw std::runtime_error(msg);
            }
            const auto now = std::chrono::steady_clock::now();
            if (now >= next_send_error_log_) {
                std::cerr << "milk-ddp: " << msg << " (continuing)\n";
                next_send_error_log_ = now + std::chrono::seconds(1);
            }
            // Drop the rest of this frame; try again on the next frame.
            return;
        }
        offset += chunk;
    }
}
