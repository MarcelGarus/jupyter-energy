#!/usr/bin/env python

import ctypes
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


if __name__ == '__main__':
    ongoing_recording = record_energy("energy-pkg")
    for i in range(3):
        sleep(1)
        print(f"Joules: {ongoing_recording.used_joules()}")
