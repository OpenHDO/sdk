cmake_minimum_required(VERSION 3.24)

project(openhdo_sdk VERSION 0.1.0 LANGUAGES CXX)

include(CTest)

option(OPENHDO_SDK_BUILD_TESTS "Build OpenHDO SDK tests" ${BUILD_TESTING})

add_library(openhdo_sdk INTERFACE)
target_compile_features(openhdo_sdk INTERFACE cxx_std_20)
target_include_directories(openhdo_sdk
    INTERFACE
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
        $<INSTALL_INTERFACE:include>
)

if(OPENHDO_SDK_BUILD_TESTS)
    add_executable(openhdo_sdk_tests tests/model.cpp)
    target_link_libraries(openhdo_sdk_tests PRIVATE openhdo_sdk)
    target_compile_features(openhdo_sdk_tests PRIVATE cxx_std_20)
    add_test(NAME openhdo_sdk_tests COMMAND openhdo_sdk_tests)
endif()

install(DIRECTORY include/ DESTINATION include)
