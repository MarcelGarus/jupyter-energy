

import ctypes
import itertools
import json
import os.path as osp
import time
from collections import deque
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from math import ceil, floor
from threading import Thread

import requests
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
        # map from days to lists with joules per 15 minutes
        self.joules_per_quarter_hour = {}


sources = [
    Source('all', 'all', record_energy('energy-pkg')),
    Source('cpu', 'CPU', record_energy('energy-cores')),
    Source('ram', 'RAM', record_energy('energy-ram')),
    Source('gpu', 'Integrated GPU', record_energy('energy-gpu')),
]


# Is called every second
def tick():
    for source in sources:
        joules = source.recording.used_joules()
        source.watts = joules - source.joules
        source.joules = joules

        source.watts_over_time.append(source.watts)
        if len(source.watts_over_time) > 100:
            source.watts_over_time.popleft()

        now = datetime.now()
        beginning_of_day = datetime(now.year, now.month, now.day, 0, 0, 0)
        quarter_hours_since_beginning_of_day = ceil((
            now - beginning_of_day).total_seconds() / (60 * 15))
        day = beginning_of_day.strftime('%Y-%m-%d')
        if day not in source.joules_per_quarter_hour:
            source.joules_per_quarter_hour[day] = []
        while len(source.joules_per_quarter_hour[day]) < quarter_hours_since_beginning_of_day - 1:
            source.joules_per_quarter_hour[day].append(0)
        if len(source.joules_per_quarter_hour[day]) < quarter_hours_since_beginning_of_day:
            source.joules_per_quarter_hour[day].append(source.watts)
        else:
            source.joules_per_quarter_hour[day][quarter_hours_since_beginning_of_day - 1] += source.watts


def monitor():
    start_time = time.time()
    interval = 1
    for i in itertools.count():
        if not running:
            return
        time.sleep(max(0, start_time + i*interval - time.time()))
        tick()
