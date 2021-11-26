#!/usr/bin/env python

import ctypes
from time import sleep

measure = ctypes.CDLL("./measure.so")
start_recording_energy = measure.start_recording_energy
start_recording_energy.restype = ctypes.c_long
energy_recording_state_in_joules = measure.energy_recording_state_in_joules
energy_recording_state_in_joules.restype = ctypes.c_double
stop_recording_energy = measure.stop_recording_energy

handle = start_recording_energy(b"energy-pkg")
print(f"Created handle: {handle}")
for i in range(3):
    sleep(1)
    joules = energy_recording_state_in_joules(handle)
    print(f"Joules: {joules}")

print("Closing")
stop_recording_energy(handle)

# class linux_dirent(ctypes.Structure):
#     _fields_ = [
#         ('d_ino', ctypes.c_long),
#         ('d_off', off_t),
#         ('d_reclen', ctypes.c_ushort),
#         ('d_name', ctypes.c_char)
#     ]

# _getdents = ctypes.CDLL(None).syscall
# _getdents.restype = ctypes.c_int
# _getdents.argtypes = ctypes.c_long, ctypes.c_uint, ctypes.POINTER(
#     ctypes.c_char), ctypes.c_uint


# libc = ctypes.CDLL(None)
# syscall = libc.syscall

# pid = syscall(39)
# print(pid)

# # This resembles the perf_event_open syscall.
# def perf_event_open(hw_event, pid, cpu, group_fd, flags):
#     syscall(libc.__NR_perf_event_open, hw_event, pid, cpu, group_fd, flags)

# long perf_event_open(struct perf_event_attr * hw_event, pid_t pid,
#                             int cpu, int group_fd, unsigned long flags)
# {
#     return syscall(__NR_perf_event_open, hw_event, pid, cpu, group_fd, flags)
# }


# struct perf_event_attr attr
# memset( & attr, 0, sizeof(attr))
# attr.type = type
# attr.size = sizeof(attr)
# attr.config = config

# perf_event_open(
#     attr,
#     -1,  # pid is not supported
#     0,  # default cpu?
#     - 1,  # group_fd is not supported
#     0  # no flags
# )

# import cffi as ffi

# libc = ffi.open("libc.so.6")
# time = libc.func("i", "time", "p")
# print("UNIX time is:", time(None))


# import io
# import sys
# from os import wait


# # Given an event name like "energy-pkg", returns a tuple containing the event
# # type, the scale, and the unit.
# def event_tuple(event: str):
#     base_path = f'/sys/bus/event_source/devices/power/events/{event}'
#     return (
#         open(base_path, 'r').read().strip(),
#         float(open(f'{base_path}.scale', 'r').read().strip()),
#         open(f'{base_path}.unit', 'r').read().strip(),
#     )


# print(event_tuple('energy-pkg'))
# event_type, scale, unit = event_tuple('energy-pkg')
