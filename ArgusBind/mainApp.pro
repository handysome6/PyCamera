
INCLUDEPATH += . \
    $$PWD/third_party/include \
    $$PWD/third_party/utils \
    $$PWD/third_party/include/libjpeg-8b \
    /usr/local/include \
    /usr/local/include/opencv4



LIBS += \
	-lNvJpegEncoder -lNvEglRenderer -lNvLogging \
	-lNvElementProfiler -lNvElement -lThread \
	-lpthread -lv4l2 -lEGL -lGLESv2 -lX11 \
	-lnvbuf_utils -lnvjpeg -lnvosd -ldrm \
	-lnveglstream_camconsumer -lnvargus_socketclient \
	-L"/usr/lib/aarch64-linux-gnu" \
	-L"/usr/lib/aarch64-linux-gnu/tegra" \
	-L"$$PWD/third_party/libs" 
