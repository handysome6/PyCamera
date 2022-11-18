cmake_minimum_required(VERSION 3.1)
cmake_policy(VERSION 3.1)

project(SampleBinding)


# ================================ General configuration ======================================

set(CMAKE_CXX_STANDARD 11)

set(CMAKE_PREFIX_PATH ${CMAKE_PREFIX_PATH} "/opt/Qt5.15/")
# Find required Qt packages.
find_package(Qt5 COMPONENTS Core Gui Widgets Concurrent REQUIRED)

if (Qt5_FOUND)
    message("Qt5 found")
endif()

set(sample_library "libcambind")
set(bindings_library "Cambind")

set(wrapped_header ${CMAKE_SOURCE_DIR}/bindings.h)
set(typesystem_file ${CMAKE_SOURCE_DIR}/bindings.xml)

set(generated_sources
    ${CMAKE_CURRENT_BINARY_DIR}/${bindings_library}/cambind_module_wrapper.cpp
    ${CMAKE_CURRENT_BINARY_DIR}/${bindings_library}/cameraholder_wrapper.cpp)


# ================================== Shiboken detection ======================================
# Use provided python interpreter if given.
if(NOT python_interpreter)
    find_program(python_interpreter "python")
endif()
message(STATUS "Using python interpreter: ${python_interpreter}")

# Macro to get various pyside / python include / link flags and paths.
# Uses the not entirely supported utils/pyside2_config.py file.
macro(pyside2_config option output_var)
    if(${ARGC} GREATER 2)
        set(is_list ${ARGV2})
    else()
        set(is_lisincludet "")
    endif()

    execute_process(
      COMMAND ${python_interpreter} "${CMAKE_SOURCE_DIR}/pyside2_config.py"
              ${option}
      OUTPUT_VARIABLE ${output_var}
      OUTPUT_STRIP_TRAILING_WHITESPACE)

    if ("${${output_var}}" STREQUAL "")
        message(FATAL_ERROR "Error: Calling pyside2_config.py ${option} returned no output.")
    endif()
    if(is_list)
        string (REPLACE " " ";" ${output_var} "${${output_var}}")
    endif()
endmacro()

# Query for the shiboken generator path, Python path, include paths and linker flags.
pyside2_config(--shiboken2-module-path shiboken2_module_path)
pyside2_config(--shiboken2-generator-path shiboken2_generator_path)
pyside2_config(--python-include-path python_include_dir)
pyside2_config(--shiboken2-generator-include-path shiboken_include_dir 1)
pyside2_config(--shiboken2-module-shared-libraries-cmake shiboken_shared_libraries 0)
pyside2_config(--python-link-flags-cmake python_linking_data 0)

###-----------------------------------------------------------------------------------
pyside2_config(--pyside2-path PYSIDE2_PATH)
pyside2_config(--pyside2-include-path PYSIDE2_INCLUDE_DIR 1)
pyside2_config(--pyside2-shared-libraries-cmake PYSIDE2_SHARED_LIBRARIES 0)

set(shiboken_path "${shiboken2_generator_path}/shiboken2${CMAKE_EXECUTABLE_SUFFIX}")
if(NOT EXISTS ${shiboken_path})
    message(FATAL_ERROR "Shiboken executable not found at path: ${shiboken_path}")
endif()

# Get all relevant Qt include dirs, to pass them on to shiboken.
get_property(QT_CORE_INCLUDE_DIRS TARGET Qt5::Core PROPERTY INTERFACE_INCLUDE_DIRECTORIES)
get_property(QT_GUI_INCLUDE_DIRS TARGET Qt5::Gui PROPERTY INTERFACE_INCLUDE_DIRECTORIES)
get_property(QT_WIDGETS_INCLUDE_DIRS TARGET Qt5::Widgets PROPERTY INTERFACE_INCLUDE_DIRECTORIES)

set(Jetson_INCLUDE_DIRS 
    ${CMAKE_SOURCE_DIR}
    ${CMAKE_SOURCE_DIR}/third_party/include 
    ${CMAKE_SOURCE_DIR}/third_party/utils 
    ${CMAKE_SOURCE_DIR}/third_party/include/libjpeg-8b )
set(Jetson_LIBS 
    -lpthread -lv4l2 -lEGL -lGLESv2 -lX11 
    -lnvbuf_utils -lnvjpeg -lnvosd -ldrm 
    -lnveglstream_camconsumer -lnvargus_socketclient 
    -L"/usr/lib/aarch64-linux-gnu" 
    -L"/usr/lib/aarch64-linux-gnu/tegra" 
    -L"${CMAKE_SOURCE_DIR}/third_party/libs" )
    
set(QT_INCLUDE_DIRS ${QT_CORE_INCLUDE_DIRS} ${QT_GUI_INCLUDE_DIRS} ${QT_WIDGETS_INCLUDE_DIRS} ${Jetson_INCLUDE_DIRS})
set(INCLUDES "")
foreach(INCLUDE_DIR ${QT_INCLUDE_DIRS})
    list(APPEND INCLUDES "-I${INCLUDE_DIR}")
endforeach()



###-----------------------------------------------------------------------------------
# We need to include the headers for the module bindings that we use.
set(PYSIDE2_ADDITIONAL_INCLUDES "")
foreach(INCLUDE_DIR ${PYSIDE2_INCLUDE_DIR})
    list(APPEND PYSIDE2_ADDITIONAL_INCLUDES "${INCLUDE_DIR}/QtCore")
    list(APPEND PYSIDE2_ADDITIONAL_INCLUDES "${INCLUDE_DIR}/QtGui")
    list(APPEND PYSIDE2_ADDITIONAL_INCLUDES "${INCLUDE_DIR}/QtWidgets")
endforeach()

# ==================================== RPATH configuration ====================================


# =============================================================================================
# !!! (The section below is deployment related, so in a real world application you will want to
# take care of this properly with some custom script or tool).
# =============================================================================================
# Enable rpaths so that the built shared libraries find their dependencies.
set(CMAKE_SKIP_BUILD_RPATH FALSE)
set(CMAKE_BUILD_WITH_INSTALL_RPATH TRUE)
set(CMAKE_INSTALL_RPATH ${shiboken2_module_path} ${CMAKE_CURRENT_SOURCE_DIR} ${PYSIDE2_PATH})
set(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)
# =============================================================================================
# !!! End of dubious section.
# =============================================================================================



# =============================== CMake target - sample_library ===============================
set(mocfile  
    cameraholder.h consumerthread.h providerthread.h sessionholder.h)#包含qobject的文件
QT5_WRAP_CPP(HEADER_MOCS ${mocfile})
set(${sample_library}_sources  
    cameraholder.cpp  consumerthread.cpp 
    providerthread.cpp sessionholder.cpp
    NvEglRenderer.cpp NvElement.cpp NvElementProfiler.cpp
    NvJpegEncoder.cpp NvLogging.cpp Thread.cpp
    ${HEADER_MOCS})
add_library(${sample_library} SHARED ${${sample_library}_sources})
target_link_libraries(${sample_library} PRIVATE Qt5::Widgets) ########
set_property(TARGET ${sample_library} PROPERTY PREFIX "")
target_compile_definitions(${sample_library} PRIVATE BINDINGS_BUILD)


# ====================== Shiboken target for generating binding C++ files  ====================
# Set up the options to pass to shiboken.
set(shiboken_options --generator-set=shiboken --enable-parent-ctor-heuristic
    --enable-return-value-heuristic --use-isnull-as-nb_nonzero --enable-pyside-extensions
    --avoid-protected-hack
    ${INCLUDES}###-------------------------------------------------------
    -I${CMAKE_SOURCE_DIR}
    -T${CMAKE_SOURCE_DIR}
    -T${PYSIDE2_PATH}/typesystems
    --output-directory=${CMAKE_CURRENT_BINARY_DIR}
    )

set(generated_sources_dependencies ${wrapped_header} ${typesystem_file})

# Add custom target to run shiboken to generate the binding cpp files.
add_custom_command(OUTPUT ${generated_sources}
                    COMMAND ${shiboken_path}
                    ${shiboken_options} ${wrapped_header} ${typesystem_file}
                    DEPENDS ${generated_sources_dependencies}
                    IMPLICIT_DEPENDS CXX ${wrapped_header}
                    WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
                    COMMENT "Running generator for ${typesystem_file}.")


# =============================== CMake target - bindings_library =============================
set(${bindings_library}_sources ${generated_sources})
add_library(${bindings_library} MODULE ${${bindings_library}_sources})
target_include_directories(${bindings_library} PRIVATE ${python_include_dir})#########
target_include_directories(${bindings_library} PRIVATE ${shiboken_include_dir})#########
target_include_directories(${bindings_library} PRIVATE ${CMAKE_SOURCE_DIR})#########
target_include_directories(${bindings_library} PRIVATE ${PYSIDE2_INCLUDE_DIR})#########
target_include_directories(${bindings_library} PRIVATE ${PYSIDE2_ADDITIONAL_INCLUDES})#########

target_link_libraries(${bindings_library} PRIVATE ${shiboken_shared_libraries})
target_link_libraries(${bindings_library} PRIVATE ${sample_library})
target_link_libraries(${bindings_library} PRIVATE Qt5::Widgets)
target_link_libraries(${bindings_library} PRIVATE ${PYSIDE2_SHARED_LIBRARIES})#pyside2.abi3.lib


set(CMAKE_CXX_FLAGS                " ${CMAKE_CXX_FLAGS_INIT} -std=c++11 -fPIC")

# inlcude and link jetson api
target_include_directories(${sample_library} PRIVATE ${Jetson_INCLUDE_DIRS})
target_include_directories(${bindings_library} PRIVATE ${Jetson_INCLUDE_DIRS})
target_link_libraries(${sample_library} PRIVATE ${Jetson_LIBS})

##一些打印信息
message( "PYSIDE2_PATH: ${PYSIDE2_PATH}")
message( "PYSIDE2_INCLUDE_DIR: ${PYSIDE2_INCLUDE_DIR}")
message( "PYSIDE2_ADDITIONAL_INCLUDES: ${PYSIDE2_ADDITIONAL_INCLUDES}")
message( "PYSIDE2_SHARED_LIBRARIES: ${PYSIDE2_SHARED_LIBRARIES}")
message( "python_include_dir: ${python_include_dir}")
message( "shiboken_include_dir: ${shiboken_include_dir}")
message( "shiboken_shared_libraries: ${shiboken_shared_libraries}")
message( "QT_INCLUDE_DIRS: ${QT_INCLUDE_DIRS}")
message( "sample_library: ${sample_library}")
message( "CMAKE_SOURCE_DIR: ${CMAKE_SOURCE_DIR}")
message( "CMAKE_CURRENT_BINARY_DIR: ${CMAKE_CURRENT_BINARY_DIR}")


# Adjust the name of generated module.
set_property(TARGET ${bindings_library} PROPERTY PREFIX "")
set_property(TARGET ${bindings_library} PROPERTY OUTPUT_NAME
             "${bindings_library}${PYTHON_EXTENSION_SUFFIX}")


# =============================================================================================
# !!! (The section below is deployment related, so in a real world application you will want to
# take care of this properly with some custom script or tool).
# =============================================================================================
# Install the library and the bindings module into the source folder near the main.py file, so
# that the Python interpeter successfully imports the used module.
install(TARGETS ${bindings_library} ${sample_library}
        LIBRARY DESTINATION ${CMAKE_SOURCE_DIR}/..
        )
# =============================================================================================
# !!! End of dubious section.
# =============================================================================================
