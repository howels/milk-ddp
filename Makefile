# Local binary and container images for milkdrop-ddp.
#
#   make              → configure + build ./build/milkdrop-ddp
#   make validate     → headless DDP self-test (no display)
#   make docker       → Debian and Alpine images
#   make docker-debian / make docker-alpine → one image

CMAKE       ?= cmake
BUILD_DIR   ?= build
BUILD_TYPE  ?= Release
JOBS        ?= $(shell nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)

# libprojectM: leave empty for FetchContent / third_party/projectm auto-detect.
# Examples:
#   make PROJECTM_SOURCE=/opt/src/projectm
#   make USE_SYSTEM_PROJECTM=1
#   make OFFLINE=1   # requires a prior download or PROJECTM_SOURCE / third_party
PROJECTM_SOURCE      ?=
USE_SYSTEM_PROJECTM  ?= 0
OFFLINE              ?= 0
CMAKE_EXTRA_ARGS     ?=

CMAKE_ARGS = -DCMAKE_BUILD_TYPE=$(BUILD_TYPE) $(CMAKE_EXTRA_ARGS)
ifneq ($(strip $(PROJECTM_SOURCE)),)
CMAKE_ARGS += -DMILKDROP_DDP_PROJECTM_SOURCE=$(PROJECTM_SOURCE)
endif
ifeq ($(USE_SYSTEM_PROJECTM),1)
CMAKE_ARGS += -DMILKDROP_DDP_USE_SYSTEM_PROJECTM=ON
endif
ifeq ($(OFFLINE),1)
CMAKE_ARGS += -DFETCHCONTENT_FULLY_DISCONNECTED=ON
endif

IMAGE       ?= milkdrop-ddp
IMAGE_DEBIAN ?= $(IMAGE):debian
IMAGE_ALPINE ?= $(IMAGE):alpine
IMAGE_LATEST ?= $(IMAGE):latest

DOCKER      ?= docker
DOCKERFILE_DEBIAN ?= Dockerfile.debian
DOCKERFILE_ALPINE ?= Dockerfile.alpine

.PHONY: all build reconfigure clean distclean validate help \
        vendor-projectm docker docker-debian docker-alpine docker-run

all: build

help:
	@printf '%s\n' \
		'make / make build     Configure and build $(BUILD_DIR)/milkdrop-ddp' \
		'make reconfigure      Wipe CMake cache and rebuild (after moving the tree)' \
		'make validate         Headless DDP stream self-test' \
		'make clean            Remove object files (keep CMake cache)' \
		'make distclean        Remove $(BUILD_DIR)/ entirely' \
		'make vendor-projectm  Clone libprojectM v4.1.8 into third_party/projectm' \
		'make PROJECTM_SOURCE=/path  Build against a local libprojectM tree' \
		'make USE_SYSTEM_PROJECTM=1  Use find_package(projectM4)' \
		'make OFFLINE=1        Do not contact the network (needs local projectM)' \
		'make docker           Build Debian and Alpine container images' \
		'make docker-debian    Build $(IMAGE_DEBIAN) (and tag :latest)' \
		'make docker-alpine    Build $(IMAGE_ALPINE)' \
		'make docker-run       Run $(IMAGE_LATEST) --help on the host network'

$(BUILD_DIR)/build.ninja $(BUILD_DIR)/Makefile: CMakeLists.txt
	$(CMAKE) -S . -B $(BUILD_DIR) $(CMAKE_ARGS)

build: $(BUILD_DIR)/build.ninja $(BUILD_DIR)/Makefile
	$(CMAKE) --build $(BUILD_DIR) -j$(JOBS)

reconfigure:
	rm -rf $(BUILD_DIR)
	$(CMAKE) -S . -B $(BUILD_DIR) $(CMAKE_ARGS)
	$(CMAKE) --build $(BUILD_DIR) -j$(JOBS)

vendor-projectm:
	@mkdir -p third_party
	@if [ -e third_party/projectm/.git ]; then \
		printf 'third_party/projectm already present\n'; \
	else \
		git clone --branch v4.1.8 --depth 1 --recurse-submodules \
			https://github.com/projectM-visualizer/projectm.git \
			third_party/projectm; \
	fi
	@printf 'Offline builds: make OFFLINE=1   (or omit network; third_party is auto-detected)\n'

clean:
	@if [ -d $(BUILD_DIR) ]; then $(CMAKE) --build $(BUILD_DIR) --target clean; fi

distclean:
	rm -rf $(BUILD_DIR)

validate: build
	bash tests/validate.sh

docker: docker-debian docker-alpine

docker-debian:
	$(DOCKER) build -f $(DOCKERFILE_DEBIAN) -t $(IMAGE_DEBIAN) -t $(IMAGE_LATEST) .

docker-alpine:
	$(DOCKER) build -f $(DOCKERFILE_ALPINE) -t $(IMAGE_ALPINE) .

docker-run:
	$(DOCKER) run --rm --network host $(IMAGE_LATEST) \
		--software-gl --preset-path /usr/share/milkdrop-ddp/presets --help
