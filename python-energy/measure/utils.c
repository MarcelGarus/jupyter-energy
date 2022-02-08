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

// First, here are some utility functions that are used in the rest of this
// file.

/// Reads the file at the given path and returns its content with trailing
/// whitespace stripped.
///
/// Returns:
/// positive: A pointer to the content.
/// 0:        The file couldn't be read. Most likely, the file doesn't exist or
///           this program doesn't have access.
///
/// Ownership: Borrows the path. Gives the caller ownership of the content.
char *_read_stripped_file(char *path)
{
    FILE *file = fopen(path, "rb");
    if (!file)
        return 0;
    char *buffer = malloc(1024);
    if (!buffer)
        return 0;
    size_t length = fread(buffer, 1, 1024, file);
    fclose(file);
    buffer[length] = '\0';
    while (buffer[strlen(buffer) - 1] == '\n' || buffer[strlen(buffer) - 1] == ' ')
    {
        buffer[strlen(buffer) - 1] = '\0';
    }
    return buffer;
}

/// Concatenates the three given strings.
///
/// Ownership: Borrows the three strings. Gives the caller ownership of the
/// result.
char *_concat_strings(char *first, char *second, char *third)
{
    char *result = malloc(sizeof(char) * (strlen(first) + strlen(second) + strlen(third) + 1));
    sprintf(result, "%s%s%s", first, second, third);
    return result;
}

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
