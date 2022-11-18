g++ -c *.cpp \
    -I../include \
    -I../utils \
    -I../include/libjpeg-8b 

ar rvs libutils.a *.o