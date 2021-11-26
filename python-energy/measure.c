#include <linux/perf_event.h>
#include <sys/syscall.h>
#include <unistd.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <errno.h>
#include <stdbool.h>

char *read_file(char *path)
{
    char *buffer = 0;
    long length;
    FILE *f = fopen(path, "rb");

    if (f)
    {
        fseek(f, 0, SEEK_END);
        length = ftell(f);
        fseek(f, 0, SEEK_SET);
        buffer = malloc(length);
        if (buffer)
        {
            fread(buffer, 1, length, f);
        }
        fclose(f);
    }

    if (buffer)
    {
        return buffer;
    }
    else
    {
        printf("Couldn't read %s.\n", path);
        exit(-103);
    }
}

int power_type()
{
    char *file_content = read_file("/sys/bus/event_source/devices/power/type");
    long type = strtol(file_content, NULL, 10);
    return type;
}

int event_config(char *event)
{
    char *basepath = "/sys/bus/event_source/devices/power/events/";
    char path[strlen(basepath) + strlen(event) + 1];
    strcpy(path, basepath);
    strcat(path, event);

    char *file_content = read_file(path);
    char *prefix = "event=0x";
    if (0 != strncmp(prefix, file_content, strlen(prefix)))
    {
        printf("Event type file has invalid content: %s\n", file_content);
        exit(-104);
    }
    long config = strtol(file_content + strlen(prefix), NULL, 16);
    return config;
}

static long perf_event_open(struct perf_event_attr *hw_event, pid_t pid,
                            int cpu, int group_fd, unsigned long flags)
{
    return syscall(__NR_perf_event_open, hw_event, pid, cpu, group_fd, flags);
}

void dump_current_ticks(long perf_fd)
{
    long int current_ticks;
    if (read(perf_fd, &current_ticks, sizeof(long int)) != sizeof(long int))
    {
        printf("Can't read event. (errno %d)\n", errno);
        exit(-101);
    }
    printf("current_ticks = %ld\n", current_ticks);
}

void main()
{
    printf("Hello, world!\n");

    int type = power_type();
    printf("Type: %d\n", type);

    int config = event_config("energy-pkg");
    printf("Event config: %d\n", config);

    struct perf_event_attr attr;
    memset(&attr, 0, sizeof(attr));
    attr.type = type;
    attr.size = sizeof(attr);
    attr.config = config;

    // Note: You can reliably debug the syscall arguments by running `strace -tT sudo ./measure`.
    long perf_fd = perf_event_open(
        &attr,
        -1, // pid is not supported
        0,  // default cpu?
        -1, // group_fd is not supported
        0   // no flags
    );
    if (perf_fd < 0)
    {
        printf("Failed to execute perf_event_open. (errno %d)", errno);
        exit(-100);
    }
    printf("perf_fd = %ld\n", perf_fd);

    while (true)
    {
        // TODO: Multiply ticks with joules per tick
        dump_current_ticks(perf_fd);
        sleep(1);
    }
}
