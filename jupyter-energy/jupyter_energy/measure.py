import ctypes
import os.path as osp
import subprocess

HERE = osp.abspath(osp.dirname(__file__))

# def __init__():
#    print("Initializing measure.py.")
#    print(subprocess.run(["pwd"]))


class OngoingEnergyRecording:
    # TODO: Add error handling.

    # dll = ctypes.CDLL(osp.join(HERE, "measure_dll.so"))

    def __init__(self, event_type: str):
        # start_recording_energy = self.dll.start_recording_energy
        # start_recording_energy.restype = ctypes.c_long
        # self.handle = start_recording_energy(event_type.encode("utf-8"))
        pass

    def used_joules(self):
        return 0.0
        # energy_recording_state_in_joules = self.dll.energy_recording_state_in_joules
        # energy_recording_state_in_joules.restype = ctypes.c_double
        # return energy_recording_state_in_joules(self.handle)

    def __del__(self):
        # stop_recording_energy = self.dll.stop_recording_energy
        # stop_recording_energy(self.handle)
        pass


def record_energy(event_type: str):
    return OngoingEnergyRecording(event_type)
