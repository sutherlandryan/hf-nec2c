/* SPDX-License-Identifier: BSD-2-Clause */
/*
 * Project-authored maintained portability code.
 * Original NEC2C source provenance remains documented by this repository.
 */

#ifndef PLATFORM_TIME_H
#define PLATFORM_TIME_H 1

/*
 * MSYS and Cygwin retain the original POSIX timing route even though their
 * compilers also define _WIN32. Native MinGW/UCRT64 uses GetProcessTimes().
 */
#if defined(_WIN32) && !defined(__CYGWIN__) && !defined(__MSYS__)
#define NEC2C_PROCESS_TIME_NATIVE_WINDOWS 1
#include <windows.h>
#else
#include <sys/times.h>
#endif

#endif /* PLATFORM_TIME_H */
