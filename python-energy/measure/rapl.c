// This file defines both a library and a standalone program:
//
// * To use it as a library, run `gcc --shared rapl.c -o rapl.so`. See the
//   `main` function at the bottom of this file for how to use the library.
// * To use it as a program, run `gcc rapl.c -o rapl && ./rapl`.
//
// This library is basically a very very stripped down version of the core
// functionality of [Pinpoint](https://github.com/osmhpi/pinpoint) with a very
// slim API on top.

#include "utils.c"

/// When users of this library start tracking an energy event, they are given a
/// pointer to this handle. They should treat it as an opaque token (not look at
/// the content) and instead only use it for further communication with this
/// library, such as reading out the energy consumption since the token creation
/// or dropping it.
typedef struct RaplHandle
{
    long file_descriptor;
    double joules_per_tick;
    long int ticks_at_creation;
} RaplHandle;

/// Starts capturing events and returns a handle that allows you to request the
/// energy currently consumed as joules.
///
/// Returns:
/// positive: Everything went successful. This is a RaplHandle.
/// negative: One of the errors defined in utils.
///
/// Ownership: Borrows input. Gives caller ownership of returned handle.
RaplHandle *create_handle(char *event)
{
    char *base_path = "/sys/bus/event_source/devices/power/events/";

    // Determine the power type.
    char *power_type_str = _read_stripped_file("/sys/bus/event_source/devices/power/type");
    if (power_type_str == 0)
        return (RaplHandle *)ERR_CANNOT_ACCESS_POWER_MEASUREMENT;
    long power_type = strtol(power_type_str, NULL, 10);
    free(power_type_str);

    // Make sure the energy is measured in joules.
    char *unit = _read_stripped_file(_concat_strings(base_path, event, ".unit"));
    if (unit == 0)
        return (RaplHandle *)ERR_EVENT_NOT_SUPPORTED;
    if (0 != strcmp(unit, "Joules"))
    {
        printf("Unknown unit \"%s\".\n", unit);
        return (RaplHandle *)ERR_UNKNOWN_UNIT;
    }
    free(unit);

    // Determine the scale (joules per tick).
    char *scale = _read_stripped_file(_concat_strings(base_path, event, ".scale"));
    if (scale == 0)
        return (RaplHandle *)ERR_EVENT_NOT_SUPPORTED;
    double joules_per_tick = strtod(scale, NULL);
    free(scale);

    // Determine the energy config of the event. For example, "energy-pkg" and
    // "energy-cpu" have different configs.
    char *event_config_str = _read_stripped_file(_concat_strings(base_path, event, ""));
    if (event_config_str == 0)
        return (RaplHandle *)ERR_EVENT_NOT_SUPPORTED;
    char *prefix = "event=0x";
    if (0 != strncmp(prefix, event_config_str, strlen(prefix)))
        return (RaplHandle *)ERR_UNEXPECTED_EVENT_CONFIG;
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
            return (RaplHandle *)ERR_MISSING_PERMISSION;
        if (errno == EINVAL || errno == ENOENT)
            return (RaplHandle *)ERR_EVENT_NOT_SUPPORTED;
        printf("syscall to perf_event_open failed for unknown reasons (errno %d)\n", errno);
        return (RaplHandle *)ERR_SYSCALL_FAILED_FOR_UNKNOWN_REASON;
    }

    // Get current number of joules.
    long int current_ticks;
    if (read(perf_file_descriptor, &current_ticks, sizeof(long int)) != sizeof(long int))
        return (RaplHandle *)ERR_COULDNT_READ_CONSUMED_ENERGY;

    // Create a handle and return it to the caller.
    RaplHandle *handle = malloc(sizeof(RaplHandle));
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
ENERGY_IN_JOULES read_handle_in_joules(RaplHandle *handle)
{
    if ((long int)handle < 0l)
        return ERR_INVALID_HANDLE;

    long int current_ticks;
    int amount_read = read(handle->file_descriptor, &current_ticks, sizeof(long int));
    if (amount_read != sizeof(long int))
        return ERR_COULDNT_READ_CONSUMED_ENERGY;

    long int ticks_since_handle_creation = current_ticks - handle->ticks_at_creation;
    ENERGY_IN_JOULES joules_since_creation = handle->joules_per_tick * (ENERGY_IN_JOULES)ticks_since_handle_creation;
    return joules_since_creation;
}

/// Drops the given handle.
///
/// Ownership: Takes ownership of the handle.
int drop_handle(RaplHandle *handle)
{
    if ((long int)handle < 0l)
        return ERR_INVALID_HANDLE;

    printf("Actually closing and freeing handle %ld.\n", (long int)handle);
    close(handle->file_descriptor);
    free(handle);

    return 0;
}

// This file can not only used as a library, but can also as a standalone
// program, which is especially useful for testing it in isolation. That's what
// the main function is for. It also shows how to use the library.

void main()
{
    printf("Hello, world! Measuring your energy consumption...\n");

    RaplHandle *handle = create_handle("energy-pkg");
    if ((long int)handle < 0)
    {
        printf("Error: Handle is %ld.\n", (long int)handle);
        exit((int)(long int)handle);
    }
    printf("Successfully created handle.\n");

    for (int i = 0; i < 3; i++)
    {
        sleep(1);
        double joules_since_start = read_handle_in_joules(handle);
        printf("Since this program started, your PC used %0.3f joules.\n", joules_since_start);
    }

    drop_handle(handle);
    printf("Recording stopped.\n");
}
