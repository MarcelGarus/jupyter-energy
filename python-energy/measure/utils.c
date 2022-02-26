// This file defines both a library and a standalone program:
//
// * To use it as a library, run `gcc --shared measure.c -o measure.so`. See the
//   `main` function at the bottom of this file for how to use the library.
// * To use it as a program, run `gcc measure.c -o measure`.
//
// This library is basically a very very stripped down version of the core
// functionality of [Pinpoint](https://github.com/osmhpi/pinpoint) with a very
// slim API on top.

#include <linux/perf_event.h>
#include <sys/syscall.h>
#include <unistd.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <errno.h>
#include <stdbool.h>

#define ENERGY_IN_JOULES double
#define POWER_IN_WATTS double

#define ERR_EVENT_NOT_SUPPORTED -1
#define ERR_UNKNOWN_UNIT -2 // Different than joules
#define ERR_CANNOT_ACCESS_POWER_MEASUREMENT -3
#define ERR_UNEXPECTED_EVENT_CONFIG -4
#define ERR_MISSING_PERMISSION -5
#define ERR_SYSCALL_FAILED_FOR_UNKNOWN_REASON -6
#define ERR_COULDNT_READ_CONSUMED_ENERGY -7
#define ERR_INVALID_HANDLE -8
#define ERR_COULDNT_WRITE_TO_MCP -9
#define ERR_COULDNT_READ_FROM_MCP -10
#define ERR_MCP_DIDNT_SEND_ACK -11
#define ERR_MCP_CHECKSUM_FAILED -12
