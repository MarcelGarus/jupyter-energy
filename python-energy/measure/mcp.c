// This file defines both a library and a standalone program:
//
// * To use it as a library, run `gcc --shared -std=gnu99 mcp.c -o mcp.so`. See
//   the `main` function at the bottom of this file for how to use the library.
// * To use it as a program, run `gcc -std=gnu99 mcp.c -o mcp && ./mcp`.
//
// This library is basically a very very stripped down version of the core
// functionality of [Pinpoint](https://github.com/osmhpi/pinpoint) with a very
// slim API on top.

#include "utils.c"
#include "mcp_com.c"
#include <dirent.h>

#define MCP_USB_VENDOR_ID 0x04d8
#define MCP_USB_PRODUCT_ID 0x00dd

// A device that has two channels where power can be measured (corresponding to
// the two sockets on the physical device).
typedef struct McpDevice
{
    long file_descriptor;
    int data[2];
    bool has_read[2];
} McpDevice;

McpDevice *create_device(char *filename)
{
    // Open the file descriptor.
    long file_descriptor = f511_init(filename);
    if (file_descriptor < 0)
    {
        if (errno == EACCES)
            return (McpDevice *)ERR_MISSING_PERMISSION;
        if (errno == ENOENT)
            return (McpDevice *)ERR_EVENT_NOT_SUPPORTED;
        printf("Couldn't access device for unknown reasons (errno %d)\n", errno);
        return (McpDevice *)ERR_SYSCALL_FAILED_FOR_UNKNOWN_REASON;
    }

    // Create a device and return it to the caller.
    McpDevice *device = malloc(sizeof(McpDevice));
    device->file_descriptor = file_descriptor;
    for (int channel = 0; channel < 2; channel++)
    {
        device->data[channel] = 0;
        device->has_read[channel] = true;
    }
    return device;
}

long int _read_device(McpDevice *device, int channel)
{
    if ((long int)device < 0)
        return ERR_INVALID_HANDLE;

    if (device->has_read[channel])
    {
        f511_get_power(&device->data[0], &device->data[1], fd);
        device->has_read[0] = false;
        device->has_read[1] = false;
    }
    device->has_read[channel] = true;

    return device->data[channel];
}

int drop_device(McpDevice *device)
{
    if ((long int)device < 0)
        return ERR_INVALID_HANDLE;

    close(device->file_descriptor);
    free(device);

    return 0;
}

/// When users of this library start tracking an energy event, they are given a
/// pointer to this handle. They should treat it as an opaque token (not look at
/// the content) and instead only use it for further communication with this
/// library, such as reading out the energy consumption since the token creation
/// or dropping it.
typedef struct McpHandle
{
    McpDevice *device;
    int channel;
    long int ticks_at_creation;
} McpHandle;

/// Starts capturing events and returns a handle that allows you to request the
/// energy currently consumed as joules.
///
/// Returns:
/// positive: Everything went successful. This is an McpHandle.
/// negative: One of the errors defined in utils.
///
/// Ownership: Borrows input. Gives caller ownership of returned handle.
McpHandle *create_handle(McpDevice *device, int channel)
{
    if ((long int)device < 0)
        return (McpHandle *)ERR_INVALID_HANDLE;

    // Get current number of joules.
    long int ticks = _read_device(device, channel);
    if (ticks < 0)
        return (McpHandle *)ticks;

    // Create a handle and return it to the caller.
    McpHandle *handle = malloc(sizeof(McpHandle));
    handle->device = device;
    handle->channel = channel;
    handle->ticks_at_creation = ticks;
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
POWER_IN_WATTS read_handle_in_watts(McpHandle *handle)
{
    if ((long int)handle < 0)
        return ERR_INVALID_HANDLE;

    // MCP returns data in 10mW steps.
    long int readout = _read_device(handle->device, handle->channel);
    POWER_IN_WATTS watts = 0.01 * (POWER_IN_WATTS)readout;
    return watts;
}

/// Drops the given handle.
///
/// Ownership: Takes ownership of the handle.
int drop_handle(McpHandle *handle)
{
    if ((long int)handle < 0)
        return ERR_INVALID_HANDLE;

    free(handle);

    return 0;
}

// This file can not only used as a library, but can also as a standalone
// program, which is especially useful for testing it in isolation. That's what
// the main function is for. It also shows how to use the library.

void main()
{
    printf("Hello, world! Measuring your energy consumption...\n");

    McpDevice *device = create_device("/dev/ttyACM0");
    if ((long int)device < 0)
    {
        printf("Error: Device is %ld.\n", (long int)device);
        exit((int)(long int)device);
    }
    printf("Successfully created device.\n");

    McpHandle *handle = create_handle(device, 1);
    if ((long int)handle < 0)
    {
        printf("Error: Handle is %ld.\n", (long int)handle);
        exit((int)(long int)handle);
    }
    printf("Successfully created handle.\n");

    for (int i = 0; i < 300; i++)
    {
        usleep(100000);
        double watts = read_handle_in_watts(handle);
        printf("The MCP currently uses %0.3f watts.\n", watts);
    }

    drop_handle(handle);
    drop_device(device);
    printf("Recording stopped.\n");
}
