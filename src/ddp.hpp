#pragma once

#include <cstdint>
#include <string>
#include <vector>

class DdpSender {
public:
    DdpSender(const std::string& host, uint16_t port);
    ~DdpSender();

    DdpSender(const DdpSender&) = delete;
    DdpSender& operator=(const DdpSender&) = delete;

    void send_rgb_frame(const unsigned char* rgb, std::size_t pixel_count);

private:
    int fd_ = -1;
    uint8_t sequence_ = 1;
};
