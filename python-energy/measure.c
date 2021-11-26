// MIT-licensed by Marcel Garus in 2021.

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
    printf("_read_stripped_file(%s)\n", path);
    FILE *file = fopen(path, "rb");
    if (!file)
        return 0;

    fseek(file, 0, SEEK_END);
    long length = ftell(file);
    fseek(file, 0, SEEK_SET);
    char *buffer = malloc(length);
    if (!buffer)
        return 0;
    fread(buffer, 1, length, file);
    fclose(file);
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

// Now that we defined some utilities, this is the actual library:

/// When users of this library start tracking an energy event, they are given a
/// pointer to this handle. They should treat it as an opaque token (not look at
/// the content) and instead only use it for further communication with this
/// library, such as getting the energy consumption since the token creation or
/// freeing it.
typedef struct EnergyRecordingHandle
{
    long file_descriptor;
    double joules_per_tick;
    long int ticks_at_creation;
} EnergyRecordingHandle;

#define ENERGY_IN_JOULES double
#define ERR_EVENT_NOT_SUPPORTED -1
#define ERR_UNKNOWN_UNIT -2 // Different than joules
#define ERR_CANNOT_ACCESS_POWER_MEASUREMENT -3
#define ERR_UNEXPECTED_EVENT_CONFIG -4
#define ERR_MISSING_PERMISSION -5
#define ERR_SYSCALL_FAILED_FOR_UNKNOWN_REASON -6
#define ERR_COULDNT_READ_CONSUMED_ENERGY -7
#define ERR_INVALID_HANDLE -8

/// Starts capturing events and returns a handle that allows you to request the
/// current amount of joules.
///
/// Returns:
/// positive: Everything went successful. This is an EnergyRecordingHandle.
/// negative: One of the errors defined above.
///
/// Ownership: Borrows input. Gives caller ownership of returned handle.
EnergyRecordingHandle *start_recording_energy(char *event)
{
    printf("start_recording_energy(%s)\n", event);
    char *base_path = "/sys/bus/event_source/devices/power/events/";

    // Determine the power type.
    char *power_type_str = _read_stripped_file("/sys/bus/event_source/devices/power/type");
    printf("power_type_str = %s\n", power_type_str);
    if (power_type_str == 0)
        return (EnergyRecordingHandle *)ERR_CANNOT_ACCESS_POWER_MEASUREMENT;
    long power_type = strtol(power_type_str, NULL, 10);
    free(power_type_str);

    // Make sure the energy is measured in joules.
    char *unit = _read_stripped_file(_concat_strings(base_path, event, ".unit"));
    printf("unit = %s\n", unit);
    if (unit == 0)
        return (EnergyRecordingHandle *)ERR_EVENT_NOT_SUPPORTED;
    if (0 != strcmp(unit, "Joules"))
        return (EnergyRecordingHandle *)ERR_UNKNOWN_UNIT;
    free(unit);

    // Determine the scale (joules per tick).
    char *scale = _read_stripped_file(_concat_strings(base_path, event, ".scale"));
    printf("scale = %s\n", scale);
    if (scale == 0)
        return (EnergyRecordingHandle *)ERR_EVENT_NOT_SUPPORTED;
    double joules_per_tick = strtod(scale, NULL);
    printf("scale = %0.20f\n", joules_per_tick);
    free(scale);

    // Determine the energy config of the event. For example, "energy-pkg" and
    // "energy-cpu" have different configs.
    char *event_config_str = _read_stripped_file(_concat_strings(base_path, event, ""));
    printf("event_config_str = %s\n", event_config_str);
    if (event_config_str == 0)
        return (EnergyRecordingHandle *)ERR_EVENT_NOT_SUPPORTED;
    char *prefix = "event=0x";
    if (0 != strncmp(prefix, event_config_str, strlen(prefix)))
        return (EnergyRecordingHandle *)ERR_UNEXPECTED_EVENT_CONFIG;
    long event_config = strtol(event_config_str + strlen(prefix), NULL, 16);
    free(event_config_str);

    // Make the perf_event_open syscall.
    struct perf_event_attr attr;
    memset(&attr, 0, sizeof(attr));
    attr.type = power_type;
    attr.size = sizeof(attr);
    attr.config = event_config;
    long perf_file_descriptor = syscall(
        __NR_perf_event_open,
        &attr,
        -1, // pid is not supported
        0,  // default cpu?
        -1, // group_fd is not supported
        0   // no flags
    );
    if (perf_file_descriptor < 0)
    {
        if (errno == EACCES)
            return (EnergyRecordingHandle *)ERR_MISSING_PERMISSION;
        printf("syscall to perf_event_open failed for unknown reasons (errno %d)\n", errno);
        return (EnergyRecordingHandle *)ERR_SYSCALL_FAILED_FOR_UNKNOWN_REASON;
    }

    // Get current number of joules.
    long int current_ticks;
    if (read(perf_file_descriptor, &current_ticks, sizeof(long int)) != sizeof(long int))
        return (EnergyRecordingHandle *)ERR_COULDNT_READ_CONSUMED_ENERGY;

    // Create a handle and return it to the caller.
    EnergyRecordingHandle *handle = malloc(sizeof(EnergyRecordingHandle));
    handle->file_descriptor = perf_file_descriptor;
    handle->joules_per_tick = joules_per_tick;
    handle->ticks_at_creation = current_ticks;
    return handle;
}

/// Given a handle, this function determines the energy in joules consumed since
/// since the handle was created.
///
/// Returns:
/// positive: The number of joules since creation.
/// negative: One of the error defined above.
///
/// Ownership: Borrows the handle. Gives ownership of the energy in joules to
/// caller.
ENERGY_IN_JOULES energy_recording_state_in_joules(EnergyRecordingHandle *handle)
{
    if (handle < 0)
        return ERR_INVALID_HANDLE;

    long int current_ticks;
    int amount_read = read(handle->file_descriptor, &current_ticks, sizeof(long int));
    if (amount_read != sizeof(long int))
        return ERR_COULDNT_READ_CONSUMED_ENERGY;

    long int ticks_since_handle_creation = current_ticks - handle->ticks_at_creation;
    double joules_since_creation = handle->joules_per_tick * (ENERGY_IN_JOULES)ticks_since_handle_creation;
    return (ENERGY_IN_JOULES)joules_since_creation;
}

/// Closes the given handle.
///
/// Ownership: Takes ownership of the handle.
int stop_recording_energy(EnergyRecordingHandle *handle)
{
    if (handle < 0)
        return ERR_INVALID_HANDLE;

    close(handle->file_descriptor);
    free(handle);

    return 0;
}

// This file can not only used as a library, but can also as a standalone
// program, which is especially useful for testing it in isolation. That's what
// the main function is for. It also highlights how to use the library.

void main()
{
    printf("Hello, world!\n");
    double d = strtod("2.3283064365386962890625e-4", NULL);
    printf("Parsed double d = %0.20f\n", d);

    EnergyRecordingHandle *handle = start_recording_energy("energy-pkg");
    if (handle < 0)
    {
        printf("Error: Handle is %ld.\n", (long int)handle);
        exit((int)(long int)handle);
    }
    printf("Successfully created handle.\n");

    while (true)
    {
        sleep(1);
        double joules_since_start = energy_recording_state_in_joules(handle);
        printf("Since this program started, your PC used %0.3f joules.\n", joules_since_start);
    }

    // Note: We never get here.
    stop_recording_energy(handle); // Invalidates the handle.
}
