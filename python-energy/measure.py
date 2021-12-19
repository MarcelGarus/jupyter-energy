#!/usr/bin/env python

import ctypes
import fileinput
import json
import os.path as osp
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from time import sleep

HERE = osp.abspath(osp.dirname(__file__))


class MeasureError(Exception):
    def __init__(self, type, arg):
        super().__init__(f"{type}: {arg}")


def assert_valid(event_type, obj):
    def fail(msg): raise MeasureError(event_type, msg)
    if obj >= 0:
        return obj
    if obj == -1:
        raise fail("Event is not supported.")
    if obj == -2:
        raise fail("Unknown unit. We can only handle joules.")
    if obj == -3:
        raise fail("Cannot access power measurement.")
    if obj == -4:
        raise fail("Unexpected event config file.")
    if obj == -5:
        raise fail("Missing permissions. Try running this as sudo.")
    if obj == -6:
        raise fail("Syscall failed for unknown reason.")
    if obj == -7:
        raise fail("Couldn't read consumed energy.")
    if obj == -8:
        raise fail("Used an invalid handle.")
    raise fail("Shared library returned unknown error code.")


class OngoingEnergyRecording:
    dll = ctypes.CDLL(f"{HERE}/measure.so")

    def __init__(self, event_type: str):
        self.event_type = event_type
        self.handle = -1
        start_recording_energy = self.dll.start_recording_energy
        start_recording_energy.restype = ctypes.c_long
        self.handle = self.assert_valid(
            start_recording_energy(event_type.encode("utf-8")))

    def assert_valid(self, obj):
        return assert_valid(self.event_type, obj)

    def used_joules(self):
        energy_recording_state_in_joules = self.dll.energy_recording_state_in_joules
        energy_recording_state_in_joules.restype = ctypes.c_double
        return self.assert_valid(energy_recording_state_in_joules(self.handle))

    def __del__(self):
        stop_recording_energy = self.dll.stop_recording_energy
        self.assert_valid(stop_recording_energy(self.handle))


def record_energy(event_type: str):
    return OngoingEnergyRecording(event_type)


# When started as a standalone program, we record the energy use.

class MyServer(BaseHTTPRequestHandler):
    recording_all = record_energy("energy-pkg")
    recording_cpu = record_energy("energy-cores")
    recording_ram = record_energy("energy-ram")
    recording_gpu = record_energy("energy-gpu")

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/json")
        self.end_headers()
        self.wfile.write(bytes(json.dumps({
            "joulesUsedByAll": self.recording_all.used_joules(),
            "joulesUsedByCpu": self.recording_cpu.used_joules(),
            "joulesUsedByRam": self.recording_ram.used_joules(),
            "joulesUsedByGpu": self.recording_gpu.used_joules()
        }), "utf-8"))
        self.wfile.write(bytes("\n", "utf-8"))


if __name__ == "__main__":
    webServer = HTTPServer(("localhost", 35396), MyServer)
    print("Server started http://%s:%s" % ("localhost", 35396))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")

# if __name__ == "__main__":
#     recording_all = record_energy("energy-pkg")
#     recording_cpu = record_energy("energy-cores")
#     recording_ram = record_energy("energy-ram")
#     recording_gpu = record_energy("energy-gpu")

#     for line in fileinput.input():
#         print(json.dumps({
#             "joulesUsedByAll": recording_all.used_joules(),
#             "joulesUsedByCpu": recording_cpu.used_joules(),
#             "joulesUsedByRam": recording_ram.used_joules(),
#             "joulesUsedByGpu": recording_gpu.used_joules()
#         }))
