CMAKE_MINIMUM_REQUIRED(VERSION 3.15)

PROJECT(PARSE)
SET(TARGET_NAME "main")

# cpecify clang-c paths
SET(CLANG_C_HEADERS "C:/Program Files/LLVM/include/")
SET(CLANG_C_LIBRARIES "C:/Program Files/LLVM/lib")

# link clang-c library
IF(WIN32)
	SET(CMAKE_EXE_LINKER_FLAGS "libclang.lib")
ELSEIF()
	SET(SMAKE_EXE_LINKER_FLAGS "-llibclang")
ENDIF()

# executable
ADD_EXECUTABLE(${TARGET_NAME} main.c parse_unit.c parse_unit.h list.c list.h)

# add paths to target
TARGET_INCLUDE_DIRECTORIES(${TARGET_NAME} PRIVATE ${CLANG_C_HEADERS})		# analogue for -I option
TARGET_LINK_DIRECTORIES(${TARGET_NAME} PRIVATE ${CLANG_C_LIBRARIES})		# analogue for -L option

# directiry
SET_TARGET_PROPERTIES(${TARGET_NAME} PROPERTIES RUNTIME_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR})