cmake_minimum_required(VERSION 3.16)
project(ap-cpp-tests)

enable_testing()

find_package(GTest REQUIRED)

if (CMAKE_CXX_COMPILER_ID STREQUAL "MSVC")
    add_definitions("/source-charset:utf-8")
    # setup-googletest currently supplies static-runtime (/MT) libraries on
    # Windows. Match that runtime explicitly to avoid LNK2038/LNK2005 failures.
    set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")
elseif (CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
    # enable static analysis for gcc
    add_compile_options(-fanalyzer -Werror)
    # disable stuff that gets triggered by googletest
    add_compile_options(-Wno-analyzer-malloc-leak)
    # enable asan for gcc
    add_compile_options(-fsanitize=address)
    add_link_options(-fsanitize=address)
endif ()

add_executable(test_default)

target_include_directories(test_default
        PRIVATE
        ${GTEST_INCLUDE_DIRS}
)

target_link_libraries(test_default
        ${GTEST_BOTH_LIBRARIES}
)

add_test(
        NAME test_default
        COMMAND  test_default
)

set_property(
        TEST test_default
        PROPERTY ENVIRONMENT "ASAN_OPTIONS=allocator_may_return_null=1"
)

file(GLOB ITEMS *)
foreach(item ${ITEMS})
    if(IS_DIRECTORY ${item} AND EXISTS ${item}/CMakeLists.txt)
        message(${item})
        add_subdirectory(${item})
    endif()
endforeach()
