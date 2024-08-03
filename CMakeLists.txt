cmake_minimum_required(VERSION 3.23)

project(c--)

add_executable(c-- main.c)

add_subdirectory(module)
add_subdirectory(common)