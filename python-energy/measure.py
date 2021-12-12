#!/usr/bin/env python

import ctypes
import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from time import sleep


# TODO: Add error handling.
class OngoingEnergyRecording:
    dll = ctypes.CDLL("./measure.so")

    def __init__(self, event_type: str):
        start_recording_energy = self.dll.start_recording_energy
        start_recording_energy.restype = ctypes.c_long
        self.handle = start_recording_energy(event_type.encode("utf-8"))

    def used_joules(self):
        energy_recording_state_in_joules = self.dll.energy_recording_state_in_joules
        energy_recording_state_in_joules.restype = ctypes.c_double
        return energy_recording_state_in_joules(self.handle)

    def __del__(self):
        stop_recording_energy = self.dll.stop_recording_energy
        stop_recording_energy(self.handle)


def record_energy(event_type: str):
    return OngoingEnergyRecording(event_type)


ongoing_recording = record_energy("energy-pkg")


class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/json")
        self.end_headers()
        self.wfile.write(bytes(json.dumps({
            "joulesPerSecond": 0,
            "joulesSinceStart": ongoing_recording.used_joules()
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
