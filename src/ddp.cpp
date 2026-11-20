#include "ddp.hpp"

#include <netdb.h>
#include <sys/socket.h>
#include <unistd.h>

#include <cerrno>
#include <cstring>
#include <stdexcept>
#include <string>

namespace {
constexpr std::size_t kHeader = 10;
constexpr std::size_t kMaxRgbBytes = 1440;  // WLED DDP_CHANNELS_PER_PACKET
constexpr uint8_t kVer1 = 0x40;
constexpr uint8_t kPush = 0x01;
constexpr uint8_t kRgb24 = 0x0B;
constexpr uint8_t kDestDisplay = 1;
}  // namespace

DdpSender::DdpSender(const std::string& host, uint16_t port)
{
    addrinfo hints {};
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_DGRAM;

    addrinfo* result = nullptr;
    const int rc = getaddrinfo(host.c_str(), std::to_string(port).c_str(), &hints, &result);
    if (rc != 0 || result == nullptr) {
        throw std::runtime_error(std::string("DDP resolve failed: ") + gai_strerror(rc));
    }

    int fd = -1;
    for (addrinfo* ai = result; ai != nullptr; ai = ai->ai_next) {
        fd = ::socket(ai->ai_family, ai->ai_socktype, ai->ai_protocol);
        if (fd < 0) {
            continue;
        }
        if (::connect(fd, ai->ai_addr, ai->ai_addrlen) == 0) {
            break;
        }
        ::close(fd);
        fd = -1;
    }
    freeaddrinfo(result);

    if (fd < 0) {
        throw std::runtime_error("DDP UDP connect failed for " + host + ":" +
                                 std::to_string(port));
    }
    fd_ = fd;
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
            throw std::runtime_error(std::string("DDP send() failed: ") + std::strerror(errno));
        }
        offset += chunk;
    }
}
