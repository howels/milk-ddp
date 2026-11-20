#include "egl_offscreen.hpp"

#include <EGL/eglext.h>
#include <GL/glext.h>
#include <cstdlib>
#include <cstring>
#include <stdexcept>
#include <string>
#include <vector>

#ifndef EGL_PLATFORM_SURFACELESS_MESA
#define EGL_PLATFORM_SURFACELESS_MESA 0x31DD
#endif
#ifndef EGL_PLATFORM_DEVICE_EXT
#define EGL_PLATFORM_DEVICE_EXT 0x313F
#endif
#ifndef EGL_DRM_DEVICE_FILE_EXT
#define EGL_DRM_DEVICE_FILE_EXT 0x3233
#endif

namespace {

const char* egl_error_name()
{
    switch (eglGetError()) {
    case EGL_SUCCESS:
        return "EGL_SUCCESS";
    case EGL_NOT_INITIALIZED:
        return "EGL_NOT_INITIALIZED";
    case EGL_BAD_ACCESS:
        return "EGL_BAD_ACCESS";
    case EGL_BAD_ALLOC:
        return "EGL_BAD_ALLOC";
    case EGL_BAD_ATTRIBUTE:
        return "EGL_BAD_ATTRIBUTE";
    case EGL_BAD_CONTEXT:
        return "EGL_BAD_CONTEXT";
    case EGL_BAD_CONFIG:
        return "EGL_BAD_CONFIG";
    case EGL_BAD_CURRENT_SURFACE:
        return "EGL_BAD_CURRENT_SURFACE";
    case EGL_BAD_DISPLAY:
        return "EGL_BAD_DISPLAY";
    case EGL_BAD_SURFACE:
        return "EGL_BAD_SURFACE";
    case EGL_BAD_MATCH:
        return "EGL_BAD_MATCH";
    case EGL_BAD_PARAMETER:
        return "EGL_BAD_PARAMETER";
    case EGL_BAD_NATIVE_PIXMAP:
        return "EGL_BAD_NATIVE_PIXMAP";
    case EGL_BAD_NATIVE_WINDOW:
        return "EGL_BAD_NATIVE_WINDOW";
    case EGL_CONTEXT_LOST:
        return "EGL_CONTEXT_LOST";
    default:
        return "unknown EGL error";
    }
}

bool client_ext_has(const char* needle)
{
    const char* ext = eglQueryString(EGL_NO_DISPLAY, EGL_EXTENSIONS);
    if (ext == nullptr) {
        return false;
    }
    return std::strstr(ext, needle) != nullptr;
}

bool device_is_software(EGLDeviceEXT device)
{
    auto query = reinterpret_cast<PFNEGLQUERYDEVICESTRINGEXTPROC>(
        eglGetProcAddress("eglQueryDeviceStringEXT"));
    if (query == nullptr) {
        return false;
    }
    const char* ext = query(device, EGL_EXTENSIONS);
    return ext != nullptr && std::strstr(ext, "EGL_MESA_device_software") != nullptr;
}

EGLDisplay try_device_display(bool software_only)
{
    auto get_platform = reinterpret_cast<PFNEGLGETPLATFORMDISPLAYEXTPROC>(
        eglGetProcAddress("eglGetPlatformDisplayEXT"));
    auto query_devices = reinterpret_cast<PFNEGLQUERYDEVICESEXTPROC>(
        eglGetProcAddress("eglQueryDevicesEXT"));
    if (get_platform == nullptr || query_devices == nullptr) {
        return EGL_NO_DISPLAY;
    }
    if (!client_ext_has("EGL_EXT_platform_device") || !client_ext_has("EGL_EXT_device_base")) {
        return EGL_NO_DISPLAY;
    }

    EGLDeviceEXT devices[16];
    EGLint count = 0;
    if (!query_devices(16, devices, &count) || count <= 0) {
        return EGL_NO_DISPLAY;
    }

    for (EGLint i = 0; i < count; ++i) {
        const bool sw = device_is_software(devices[i]);
        if (software_only && !sw) {
            continue;
        }
        if (!software_only && sw) {
            continue;
        }
        EGLDisplay dpy = get_platform(EGL_PLATFORM_DEVICE_EXT, devices[i], nullptr);
        if (dpy != EGL_NO_DISPLAY) {
            return dpy;
        }
    }
    return EGL_NO_DISPLAY;
}

EGLDisplay try_display(bool software)
{
    auto get_platform = reinterpret_cast<PFNEGLGETPLATFORMDISPLAYEXTPROC>(
        eglGetProcAddress("eglGetPlatformDisplayEXT"));

    if (software) {
        EGLDisplay sw = try_device_display(true);
        if (sw != EGL_NO_DISPLAY) {
            return sw;
        }
        // Default display with GALLIUM_DRIVER=llvmpipe, not a GPU EGL device.
        EGLDisplay def = eglGetDisplay(EGL_DEFAULT_DISPLAY);
        if (def != EGL_NO_DISPLAY) {
            return def;
        }
    } else {
        EGLDisplay hw = try_device_display(false);
        if (hw != EGL_NO_DISPLAY) {
            return hw;
        }
    }

    if (get_platform != nullptr && client_ext_has("EGL_MESA_platform_surfaceless")) {
        EGLDisplay dpy =
            get_platform(EGL_PLATFORM_SURFACELESS_MESA, EGL_DEFAULT_DISPLAY, nullptr);
        if (dpy != EGL_NO_DISPLAY) {
            return dpy;
        }
    }

    return eglGetDisplay(EGL_DEFAULT_DISPLAY);
}

}  // namespace

OffscreenGL::~OffscreenGL()
{
    destroy();
}

void OffscreenGL::destroy() noexcept
{
    if (display_ == EGL_NO_DISPLAY) {
        return;
    }
    eglMakeCurrent(display_, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT);
    if (surface_ != EGL_NO_SURFACE) {
        eglDestroySurface(display_, surface_);
        surface_ = EGL_NO_SURFACE;
    }
    if (context_ != EGL_NO_CONTEXT) {
        eglDestroyContext(display_, context_);
    }
    eglTerminate(display_);
    display_ = EGL_NO_DISPLAY;
    context_ = EGL_NO_CONTEXT;
}

void OffscreenGL::create(int width, int height, bool software)
{
    width_ = width;
    height_ = height;

    // LIBGL_ALWAYS_SOFTWARE cannot be combined with EGL_EXT_platform_device
    // on a GPU node. Pin the Gallium driver instead, then pick the software
    // EGL device explicitly.
    if (software) {
        ::setenv("GALLIUM_DRIVER", "llvmpipe", 1);
        ::setenv("MESA_LOADER_DRIVER_OVERRIDE", "llvmpipe", 1);
        ::unsetenv("LIBGL_ALWAYS_SOFTWARE");
    }

    display_ = try_display(software);
    if (display_ == EGL_NO_DISPLAY) {
        throw std::runtime_error(std::string("eglGetDisplay failed: ") + egl_error_name());
    }

    EGLint major = 0;
    EGLint minor = 0;
    if (!eglInitialize(display_, &major, &minor)) {
        throw std::runtime_error(std::string("eglInitialize failed: ") + egl_error_name());
    }

    // libprojectM 4.1 composites the final frame onto OpenGL framebuffer 0.
    // That is the EGL pbuffer (or window), not a user FBO, so a pbuffer is
    // required. Surfaceless + FBO alone yields a black DDP stream.
    const EGLint pbuffer_cfg[] = {EGL_RENDERABLE_TYPE,
                                  EGL_OPENGL_BIT,
                                  EGL_SURFACE_TYPE,
                                  EGL_PBUFFER_BIT,
                                  EGL_RED_SIZE,
                                  8,
                                  EGL_GREEN_SIZE,
                                  8,
                                  EGL_BLUE_SIZE,
                                  8,
                                  EGL_DEPTH_SIZE,
                                  24,
                                  EGL_STENCIL_SIZE,
                                  8,
                                  EGL_NONE};
    const EGLint pbuffer_min[] = {EGL_RENDERABLE_TYPE, EGL_OPENGL_BIT, EGL_SURFACE_TYPE,
                                  EGL_PBUFFER_BIT, EGL_NONE};

    EGLConfig config {};
    EGLint ncfg = 0;
    if (!(eglChooseConfig(display_, pbuffer_cfg, &config, 1, &ncfg) && ncfg > 0) &&
        !(eglChooseConfig(display_, pbuffer_min, &config, 1, &ncfg) && ncfg > 0)) {
        throw std::runtime_error(std::string("eglChooseConfig found no pbuffer OpenGL config: ") +
                                 egl_error_name());
    }

    if (!eglBindAPI(EGL_OPENGL_API)) {
        throw std::runtime_error(std::string("eglBindAPI(OpenGL) failed: ") + egl_error_name());
    }

    const EGLint ctx_attribs[] = {
        EGL_CONTEXT_MAJOR_VERSION,
        3,
        EGL_CONTEXT_MINOR_VERSION,
        3,
        EGL_CONTEXT_OPENGL_PROFILE_MASK,
        EGL_CONTEXT_OPENGL_CORE_PROFILE_BIT,
        EGL_NONE,
    };

    context_ = eglCreateContext(display_, config, EGL_NO_CONTEXT, ctx_attribs);
    if (context_ == EGL_NO_CONTEXT) {
        throw std::runtime_error(std::string("eglCreateContext 3.3 core failed: ") +
                                 egl_error_name());
    }

    const EGLint pbuffer_attribs[] = {EGL_WIDTH, width_, EGL_HEIGHT, height_, EGL_NONE};
    surface_ = eglCreatePbufferSurface(display_, config, pbuffer_attribs);
    if (surface_ == EGL_NO_SURFACE) {
        throw std::runtime_error(std::string("eglCreatePbufferSurface failed: ") + egl_error_name());
    }

    if (!eglMakeCurrent(display_, surface_, surface_, context_)) {
        throw std::runtime_error(std::string("eglMakeCurrent(pbuffer) failed: ") + egl_error_name());
    }

    glBindFramebuffer(GL_FRAMEBUFFER, 0);
    glViewport(0, 0, width_, height_);
}

void OffscreenGL::bind_default() const
{
    glBindFramebuffer(GL_FRAMEBUFFER, 0);
    glViewport(0, 0, width_, height_);
}

void OffscreenGL::read_rgb(unsigned char* dest_top_left_rgb)
{
    bind_default();
    glPixelStorei(GL_PACK_ALIGNMENT, 1);
    // glReadPixels synchronises the pipeline; an extra glFinish() only adds
    // latency with no correctness benefit for this readback path.

    const std::size_t bytes = static_cast<std::size_t>(width_) * height_ * 3;
    if (readback_.size() != bytes) {
        readback_.assign(bytes, 0);
    }
    glReadPixels(0, 0, width_, height_, GL_RGB, GL_UNSIGNED_BYTE, readback_.data());
    const GLenum err = glGetError();
    if (err != GL_NO_ERROR) {
        throw std::runtime_error("glReadPixels failed with GL error " + std::to_string(err));
    }

    for (int y = 0; y < height_; ++y) {
        const unsigned char* src =
            readback_.data() + static_cast<std::size_t>(height_ - 1 - y) * width_ * 3;
        unsigned char* dst = dest_top_left_rgb + static_cast<std::size_t>(y) * width_ * 3;
        std::memcpy(dst, src, static_cast<std::size_t>(width_) * 3);
    }
}

std::string OffscreenGL::renderer_string() const
{
    const auto* vendor = reinterpret_cast<const char*>(glGetString(GL_VENDOR));
    const auto* renderer = reinterpret_cast<const char*>(glGetString(GL_RENDERER));
    const auto* version = reinterpret_cast<const char*>(glGetString(GL_VERSION));
    std::string s;
    if (vendor) {
        s += vendor;
        s += " / ";
    }
    if (renderer) {
        s += renderer;
        s += " / ";
    }
    if (version) {
        s += version;
    }
    return s;
}
