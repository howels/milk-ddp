cmake_minimum_required(VERSION 3.21)
project(milkdrop-ddp VERSION 0.1.0 LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

include(FetchContent)

# libprojectM is LGPL-2.1. Built as a static library so the runtime image
# carries one binary plus Mesa; source of the pinned tag is fetched at configure.
set(BUILD_SHARED_LIBS OFF CACHE BOOL "" FORCE)
set(ENABLE_PLAYLIST ON CACHE BOOL "" FORCE)
set(ENABLE_SDL_UI OFF CACHE BOOL "" FORCE)
set(ENABLE_INSTALL OFF CACHE BOOL "" FORCE)
set(ENABLE_SYSTEM_PROJECTM_EVAL OFF CACHE BOOL "" FORCE)
set(ENABLE_SYSTEM_GLM OFF CACHE BOOL "" FORCE)
set(BUILD_TESTING OFF CACHE BOOL "" FORCE)
set(BUILD_DOCS OFF CACHE BOOL "" FORCE)

FetchContent_Declare(
    projectm
    GIT_REPOSITORY https://github.com/projectM-visualizer/projectm.git
    GIT_TAG v4.1.8
    GIT_SHALLOW TRUE
    GIT_SUBMODULES_RECURSE TRUE
)
FetchContent_MakeAvailable(projectm)

find_package(OpenGL REQUIRED COMPONENTS OpenGL EGL)
find_package(Threads REQUIRED)
find_package(PkgConfig)

set(MILKDROP_DDP_HAVE_PULSE OFF)
if(PkgConfig_FOUND)
    pkg_check_modules(PULSE libpulse-simple)
    if(PULSE_FOUND)
        set(MILKDROP_DDP_HAVE_PULSE ON)
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

include(GNUInstallDirs)
install(TARGETS milkdrop-ddp RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR})
install(DIRECTORY presets/ DESTINATION ${CMAKE_INSTALL_DATADIR}/milkdrop-ddp/presets)
install(PROGRAMS tests/ddp_listen.py DESTINATION ${CMAKE_INSTALL_LIBEXECDIR}/milkdrop-ddp)
