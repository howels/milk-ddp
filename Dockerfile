# Debian image (same stages as Dockerfile.debian).
# Preferred release image is Alpine — use Dockerfile.alpine / make docker-alpine.
# Explicit tags: make docker-debian | make docker-alpine (Alpine also tags :latest).
FROM debian:bookworm-slim AS build

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        cmake \
        g++ \
        git \
        libegl1-mesa-dev \
        libgl1-mesa-dev \
        libglm-dev \
        libasound2-dev \
        libpulse-dev \
        make \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src
COPY CMakeLists.txt ./
COPY src ./src
COPY presets ./presets
COPY tests ./tests
# Optional offline libprojectM tree (make vendor-projectm on the host first).
COPY third_party ./third_party

RUN cmake -S . -B build -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX=/usr \
    && cmake --build build -j"$(nproc)" \
    && cmake --install build

FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        libegl1 \
        libgl1 \
        libgl1-mesa-dri \
        libasound2 \
        libpulse0 \
        mesa-utils \
        python3 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=build /usr/bin/milk-ddp /usr/bin/milk-ddp
COPY --from=build /usr/share/milk-ddp /usr/share/milk-ddp
COPY --from=build /usr/libexec/milk-ddp /usr/libexec/milk-ddp

ENV GALLIUM_DRIVER=llvmpipe \
    MESA_LOADER_DRIVER_OVERRIDE=llvmpipe

ENTRYPOINT ["/usr/bin/milk-ddp"]
CMD ["--software-gl", "--preset-path", "/usr/share/milk-ddp/presets", "--help"]
