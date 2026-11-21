cmake_minimum_required(VERSION 3.21)
project(milk-ddp VERSION 0.2.0 LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# ---------------------------------------------------------------------------
# libprojectM (LGPL-2.1). Resolution order:
#   1. MILK_DDP_USE_SYSTEM_PROJECTM=ON  → find_package(projectM4)
#   2. MILK_DDP_PROJECTM_SOURCE=<dir>   → local source tree (offline)
#   3. third_party/projectm/                → vendored checkout (offline)
#   4. FetchContent from GitHub tag         → needs network on first configure
# ---------------------------------------------------------------------------
option(MILK_DDP_USE_SYSTEM_PROJECTM
    "Link against an installed libprojectM (find_package projectM4)" OFF)
set(MILK_DDP_PROJECTM_SOURCE "" CACHE PATH
    "Path to a local libprojectM source tree. Empty uses third_party/projectm or FetchContent.")
set(MILK_DDP_PROJECTM_GIT_TAG "v4.1.8" CACHE STRING
    "Git tag / commit used when FetchContent downloads libprojectM")
set(MILK_DDP_PROJECTM_GIT_REPOSITORY
    "https://github.com/projectM-visualizer/projectm.git" CACHE STRING
    "Git remote used when FetchContent downloads libprojectM")

set(MILK_DDP_PROJECTM_MODE "")

if(MILK_DDP_USE_SYSTEM_PROJECTM)
    find_package(projectM4 REQUIRED)
    find_package(projectM4Playlist REQUIRED)
    set(MILK_DDP_PROJECTM_MODE "system (${projectM4_DIR})")
else()
    # Options that only apply when we compile libprojectM ourselves.
    set(BUILD_SHARED_LIBS OFF CACHE BOOL "" FORCE)
    set(ENABLE_PLAYLIST ON CACHE BOOL "" FORCE)
    set(ENABLE_SDL_UI OFF CACHE BOOL "" FORCE)
    set(ENABLE_INSTALL OFF CACHE BOOL "" FORCE)
    set(ENABLE_SYSTEM_PROJECTM_EVAL OFF CACHE BOOL "" FORCE)
    set(ENABLE_SYSTEM_GLM OFF CACHE BOOL "" FORCE)
    set(BUILD_TESTING OFF CACHE BOOL "" FORCE)
    set(BUILD_DOCS OFF CACHE BOOL "" FORCE)

    set(_projectm_src "")
    if(MILK_DDP_PROJECTM_SOURCE)
        set(_projectm_src "${MILK_DDP_PROJECTM_SOURCE}")
    elseif(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/third_party/projectm/CMakeLists.txt")
        set(_projectm_src "${CMAKE_CURRENT_SOURCE_DIR}/third_party/projectm")
    endif()

    if(_projectm_src)
        get_filename_component(_projectm_src "${_projectm_src}" ABSOLUTE)
        if(NOT EXISTS "${_projectm_src}/CMakeLists.txt")
            message(FATAL_ERROR
                "MILK_DDP_PROJECTM_SOURCE does not look like libprojectM: ${_projectm_src}\n"
                "Expected a checkout of https://github.com/projectM-visualizer/projectm "
                "(tag ${MILK_DDP_PROJECTM_GIT_TAG}) with its submodules initialised.")
        endif()
        message(STATUS "libprojectM: building from local source ${_projectm_src}")
        add_subdirectory("${_projectm_src}" "${CMAKE_BINARY_DIR}/_deps/projectm-build")
        set(MILK_DDP_PROJECTM_MODE "local-source (${_projectm_src})")
    else()
        include(FetchContent)
        message(STATUS
            "libprojectM: FetchContent ${MILK_DDP_PROJECTM_GIT_REPOSITORY} "
            "(${MILK_DDP_PROJECTM_GIT_TAG})")
        message(STATUS
            "  Offline? Clone into third_party/projectm or pass "
            "-DMILK_DDP_PROJECTM_SOURCE=/path/to/projectm")
        FetchContent_Declare(
            projectm
            GIT_REPOSITORY "${MILK_DDP_PROJECTM_GIT_REPOSITORY}"
            GIT_TAG "${MILK_DDP_PROJECTM_GIT_TAG}"
            GIT_SHALLOW TRUE
            GIT_SUBMODULES_RECURSE TRUE
        )
        # Re-use a previous download without contacting the network:
        #   cmake -DFETCHCONTENT_FULLY_DISCONNECTED=ON ...
        FetchContent_MakeAvailable(projectm)
        set(MILK_DDP_PROJECTM_MODE
            "fetchcontent (${MILK_DDP_PROJECTM_GIT_TAG})")
    endif()
endif()

message(STATUS "libprojectM mode: ${MILK_DDP_PROJECTM_MODE}")

# Mesa on Alpine has no GLVND libOpenGL.so. CMake's FindOpenGL COMPONENTS EGL
# still requires that library, so link via pkg-config (egl + gl) on all hosts.
find_package(Threads REQUIRED)
find_package(PkgConfig REQUIRED)
pkg_check_modules(EGL REQUIRED IMPORTED_TARGET egl)
pkg_check_modules(GL REQUIRED IMPORTED_TARGET gl)
message(STATUS "EGL: ${EGL_VERSION}  GL: ${GL_VERSION}")

set(MILK_DDP_HAVE_PULSE OFF)
set(MILK_DDP_HAVE_ALSA OFF)
if(PkgConfig_FOUND)
    pkg_check_modules(PULSE IMPORTED_TARGET libpulse)
    if(TARGET PkgConfig::PULSE)
        set(MILK_DDP_HAVE_PULSE ON)
        message(STATUS "PulseAudio: enabled (${PULSE_VERSION})")
    else()
        message(STATUS "PulseAudio: not found ( --audio pulse disabled )")
    endif()
    pkg_check_modules(ALSA IMPORTED_TARGET alsa)
    if(TARGET PkgConfig::ALSA)
        set(MILK_DDP_HAVE_ALSA ON)
        message(STATUS "ALSA: enabled (${ALSA_VERSION})")
    else()
        message(STATUS "ALSA: not found ( --audio alsa disabled )")
    endif()
endif()

add_executable(milk-ddp
    src/main.cpp
    src/cli.cpp
    src/egl_offscreen.cpp
    src/ddp.cpp
    src/audio.cpp
    src/projectm_props.cpp
)

target_include_directories(milk-ddp PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/src")

target_compile_options(milk-ddp PRIVATE
    $<$<CXX_COMPILER_ID:GNU,Clang,AppleClang>:-Wall -Wextra -Wpedantic -Wshadow>
)

target_link_libraries(milk-ddp PRIVATE
    libprojectM::projectM
    libprojectM::playlist
    PkgConfig::EGL
    PkgConfig::GL
    Threads::Threads
)

if(MILK_DDP_HAVE_PULSE)
    target_compile_definitions(milk-ddp PRIVATE HAVE_PULSE=1)
    target_link_libraries(milk-ddp PRIVATE PkgConfig::PULSE)
endif()

if(MILK_DDP_HAVE_ALSA)
    target_compile_definitions(milk-ddp PRIVATE HAVE_ALSA=1)
    target_link_libraries(milk-ddp PRIVATE PkgConfig::ALSA)
endif()

include(GNUInstallDirs)
install(TARGETS milk-ddp RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR})
install(DIRECTORY presets/ DESTINATION ${CMAKE_INSTALL_DATADIR}/milk-ddp/presets
        PATTERN "LICENSE" EXCLUDE)
install(FILES presets/LICENSE DESTINATION ${CMAKE_INSTALL_DATADIR}/milk-ddp/presets)
install(FILES presets/modern/LICENSE
        DESTINATION ${CMAKE_INSTALL_DATADIR}/milk-ddp/presets/modern)
install(FILES LICENSE THIRD_PARTY.md DESTINATION ${CMAKE_INSTALL_DOCDIR})
# Ship whatever documentation is present under docs/ (e.g. PERFORMANCE.md).
install(DIRECTORY docs/
        DESTINATION ${CMAKE_INSTALL_DOCDIR}
        FILES_MATCHING
        PATTERN "*.md"
        PATTERN "*.txt")
install(PROGRAMS tests/ddp_listen.py DESTINATION ${CMAKE_INSTALL_LIBEXECDIR}/milk-ddp)
