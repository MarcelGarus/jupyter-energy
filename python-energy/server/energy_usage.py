

import itertools
import time
from collections import deque
from datetime import datetime
from math import ceil

from measure import OngoingEnergyRecording, record_energy

from server.utils import *


class Source:
    def __init__(self, id: str, name: str, recording: OngoingEnergyRecording):
        self.id = id
        self.name = name
        self.recording = recording
        self.joules = 0
        self.watts = 0
        self.watts_over_time = deque([])
        # list with one joule value per long_term_resolution since server start
        self.long_term_joules = []


sources = [
    Source('all', 'all', record_energy('energy-pkg')),
    Source('cpu', 'CPU', record_energy('energy-cores')),
    Source('ram', 'RAM', record_energy('energy-ram')),
    Source('gpu', 'Integrated GPU', record_energy('energy-gpu')),
]


def tick():
    for source in sources:
        joules = source.recording.used_joules()
        source.watts = (joules - source.joules) / \
            short_term_resolution.total_seconds()
        source.joules = joules

        source.watts_over_time.append(source.watts)
        if len(source.watts_over_time) > 100:
            source.watts_over_time.popleft()

        index = ceil((datetime.now() - server_started) / long_term_resolution)
        while len(source.long_term_joules) < index - 1:
            source.long_term_joules.append(0)
        if len(source.long_term_joules) < index:
            source.long_term_joules.append(source.watts)
        else:
            source.long_term_joules[index - 1] += source.watts


def monitor():
    tick_repeatedly(short_term_resolution, tick)
