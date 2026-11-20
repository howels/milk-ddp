#pragma once

#include <string>

#define GL_GLEXT_PROTOTYPES 1
#include <EGL/egl.h>
#include <GL/gl.h>

class OffscreenGL {
public:
    OffscreenGL() = default;
    ~OffscreenGL();

    OffscreenGL(const OffscreenGL&) = delete;
    OffscreenGL& operator=(const OffscreenGL&) = delete;

    void create(int width, int height, bool software);
    void bind_default() const;
    void read_rgb(unsigned char* dest_top_left_rgb) const;

    int width() const { return width_; }
    int height() const { return height_; }
    std::string renderer_string() const;

private:
    void destroy() noexcept;

    EGLDisplay display_ = EGL_NO_DISPLAY;
    EGLContext context_ = EGL_NO_CONTEXT;
    EGLSurface surface_ = EGL_NO_SURFACE;
    int width_ = 0;
    int height_ = 0;
};
