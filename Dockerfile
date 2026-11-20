# Headless projectM → DDP. Mesa llvmpipe supplies OpenGL 3.3 without a GPU
# or a window system. The runtime image holds the binary, two default
# presets, and the Mesa software stack.
FROM debian:bookworm-slim AS build

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        cmake \
        g++ \
        git \
        libegl1-mesa-dev \
        libgl1-mesa-dev \
        libglm-dev \
        libpulse-dev \
        make \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src
COPY CMakeLists.txt ./
COPY src ./src
COPY presets ./presets
COPY tests ./tests

RUN cmake -S . -B build -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX=/usr \
    && cmake --build build -j"$(nproc)" \
    && cmake --install build

FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        libegl1 \
        libgl1 \
        libgl1-mesa-dri \
        libpulse0 \
        mesa-utils \
        python3 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=build /usr/bin/milkdrop-ddp /usr/bin/milkdrop-ddp
COPY --from=build /usr/share/milkdrop-ddp /usr/share/milkdrop-ddp
COPY --from=build /usr/libexec/milkdrop-ddp /usr/libexec/milkdrop-ddp

ENV LIBGL_ALWAYS_SOFTWARE=1 \
    GALLIUM_DRIVER=llvmpipe

ENTRYPOINT ["/usr/bin/milkdrop-ddp"]
CMD ["--software-gl", "--preset-path", "/usr/share/milkdrop-ddp/presets", "--help"]
