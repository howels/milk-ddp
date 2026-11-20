cmake_minimum_required(VERSION 3.21)
project(milkdrop-ddp VERSION 0.1.0 LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# ---------------------------------------------------------------------------
# libprojectM (LGPL-2.1). Resolution order:
#   1. MILKDROP_DDP_USE_SYSTEM_PROJECTM=ON  → find_package(projectM4)
#   2. MILKDROP_DDP_PROJECTM_SOURCE=<dir>   → local source tree (offline)
#   3. third_party/projectm/                → vendored checkout (offline)
#   4. FetchContent from GitHub tag         → needs network on first configure
# ---------------------------------------------------------------------------
option(MILKDROP_DDP_USE_SYSTEM_PROJECTM
    "Link against an installed libprojectM (find_package projectM4)" OFF)
set(MILKDROP_DDP_PROJECTM_SOURCE "" CACHE PATH
    "Path to a local libprojectM source tree. Empty uses third_party/projectm or FetchContent.")
set(MILKDROP_DDP_PROJECTM_GIT_TAG "v4.1.8" CACHE STRING
    "Git tag / commit used when FetchContent downloads libprojectM")
set(MILKDROP_DDP_PROJECTM_GIT_REPOSITORY
    "https://github.com/projectM-visualizer/projectm.git" CACHE STRING
    "Git remote used when FetchContent downloads libprojectM")

set(MILKDROP_DDP_PROJECTM_MODE "")

if(MILKDROP_DDP_USE_SYSTEM_PROJECTM)
    find_package(projectM4 REQUIRED)
    find_package(projectM4Playlist REQUIRED)
    set(MILKDROP_DDP_PROJECTM_MODE "system (${projectM4_DIR})")
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
    if(MILKDROP_DDP_PROJECTM_SOURCE)
        set(_projectm_src "${MILKDROP_DDP_PROJECTM_SOURCE}")
    elseif(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/third_party/projectm/CMakeLists.txt")
        set(_projectm_src "${CMAKE_CURRENT_SOURCE_DIR}/third_party/projectm")
    endif()

    if(_projectm_src)
        get_filename_component(_projectm_src "${_projectm_src}" ABSOLUTE)
        if(NOT EXISTS "${_projectm_src}/CMakeLists.txt")
            message(FATAL_ERROR
                "MILKDROP_DDP_PROJECTM_SOURCE does not look like libprojectM: ${_projectm_src}\n"
                "Expected a checkout of https://github.com/projectM-visualizer/projectm "
                "(tag ${MILKDROP_DDP_PROJECTM_GIT_TAG}) with its submodules initialised.")
        endif()
        message(STATUS "libprojectM: building from local source ${_projectm_src}")
        add_subdirectory("${_projectm_src}" "${CMAKE_BINARY_DIR}/_deps/projectm-build")
        set(MILKDROP_DDP_PROJECTM_MODE "local-source (${_projectm_src})")
    else()
        include(FetchContent)
        message(STATUS
            "libprojectM: FetchContent ${MILKDROP_DDP_PROJECTM_GIT_REPOSITORY} "
            "(${MILKDROP_DDP_PROJECTM_GIT_TAG})")
        message(STATUS
            "  Offline? Clone into third_party/projectm or pass "
            "-DMILKDROP_DDP_PROJECTM_SOURCE=/path/to/projectm")
        FetchContent_Declare(
            projectm
            GIT_REPOSITORY "${MILKDROP_DDP_PROJECTM_GIT_REPOSITORY}"
            GIT_TAG "${MILKDROP_DDP_PROJECTM_GIT_TAG}"
            GIT_SHALLOW TRUE
            GIT_SUBMODULES_RECURSE TRUE
        )
        # Re-use a previous download without contacting the network:
        #   cmake -DFETCHCONTENT_FULLY_DISCONNECTED=ON ...
        FetchContent_MakeAvailable(projectm)
        set(MILKDROP_DDP_PROJECTM_MODE
            "fetchcontent (${MILKDROP_DDP_PROJECTM_GIT_TAG})")
    endif()
endif()

message(STATUS "libprojectM mode: ${MILKDROP_DDP_PROJECTM_MODE}")

find_package(OpenGL REQUIRED COMPONENTS OpenGL EGL)
find_package(Threads REQUIRED)
find_package(PkgConfig)

set(MILKDROP_DDP_HAVE_PULSE OFF)
set(MILKDROP_DDP_HAVE_ALSA OFF)
if(PkgConfig_FOUND)
    # Async libpulse (threaded mainloop + source subscriptions) for hotplug.
    pkg_check_modules(PULSE libpulse)
    if(PULSE_FOUND)
        set(MILKDROP_DDP_HAVE_PULSE ON)
    endif()
    pkg_check_modules(ALSA alsa)
    if(ALSA_FOUND)
        set(MILKDROP_DDP_HAVE_ALSA ON)
    endif()
endif()

add_executable(milkdrop-ddp
    src/main.cpp
    src/cli.cpp
    src/egl_offscreen.cpp
    src/ddp.cpp
    src/audio.cpp
    src/projectm_props.cpp
)

target_include_directories(milkdrop-ddp PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/src")

target_link_libraries(milkdrop-ddp PRIVATE
    libprojectM::projectM
    libprojectM::playlist
    OpenGL::EGL
    OpenGL::GL
    Threads::Threads
)

if(MILKDROP_DDP_HAVE_PULSE)
    target_compile_definitions(milkdrop-ddp PRIVATE HAVE_PULSE=1)
    target_include_directories(milkdrop-ddp PRIVATE ${PULSE_INCLUDE_DIRS})
    target_link_libraries(milkdrop-ddp PRIVATE ${PULSE_LIBRARIES})
endif()

if(MILKDROP_DDP_HAVE_ALSA)
    target_compile_definitions(milkdrop-ddp PRIVATE HAVE_ALSA=1)
    target_include_directories(milkdrop-ddp PRIVATE ${ALSA_INCLUDE_DIRS})
    target_link_libraries(milkdrop-ddp PRIVATE ${ALSA_LIBRARIES})
endif()

include(GNUInstallDirs)
install(TARGETS milkdrop-ddp RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR})
install(DIRECTORY presets/ DESTINATION ${CMAKE_INSTALL_DATADIR}/milkdrop-ddp/presets)
install(PROGRAMS tests/ddp_listen.py DESTINATION ${CMAKE_INSTALL_LIBEXECDIR}/milkdrop-ddp)
