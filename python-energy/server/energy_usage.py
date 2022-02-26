

import itertools
import time
from collections import deque
from datetime import datetime
from math import ceil
from re import M

from measure import McpDevice, McpHandle, MeasureError, NvmlHandle, RaplHandle

from server.utils import *


class Source:
    def __init__(self, id: str, name: str):
        self.id = id
        self.name = name
        self.joules = 0
        self.watts = 0

        # has one watts value per short_term_resolution
        self.watts_over_time = deque([])

        # has one joules value per long_term_resolution since server start
        self.long_term_joules = []

    # called every short_term_resolution
    def tick(self):
        self.watts_over_time.append(self.watts)
        if len(self.watts_over_time) > 100:
            self.watts_over_time.popleft()

        index = ceil((datetime.now() - server_started) / long_term_resolution)
        while len(self.long_term_joules) < index - 1:
            self.long_term_joules.append(0)
        if len(self.long_term_joules) < index:
            self.long_term_joules.append(self.watts)
        else:
            self.long_term_joules[index - 1] += self.watts

    def __repr__(self):
        return self.id


class RaplSource(Source):
    def __init__(self, id: str, name: str, handle: RaplHandle):
        super().__init__(id, name)
        self.handle = handle

    def tick(self):
        joules = self.handle.used_joules()
        self.watts = 0 if joules == self.joules else \
            (joules - self.joules) / short_term_resolution.total_seconds()
        self.joules = joules
        super().tick()

class McpSource(Source):
    def __init__(self, id: str, name: str, handle: McpHandle):
        super().__init__(id, name)
        self.handle = handle

    def tick(self):
        self.joules += self.watts * short_term_resolution.total_seconds()
        self.watts = self.handle.current_watts()
        super().tick()

class NvmlSource(Source):
    def __init__(self, id: str, name: str, handle: NvmlHandle):
        super().__init__(id, name)
        self.handle = handle

    def tick(self):
        self.joules += self.watts * short_term_resolution.total_seconds()
        self.watts = self.handle.current_watts()
        super().tick()


def discover_sources():
    print("Discovering sources.")
    
    # RAPL sources
    print("Discovering RAPL.")
    rapl_sources = [
        # (internal id, user-visible name, event type)
        ('all', 'RAPL, all', 'energy-pkg'),
        ('cpu', 'RAPL, CPU', 'energy-cores'),
        ('ram', 'RAPL, RAM', 'energy-ram'),
        ('gpu', 'RAPL, integrated GPU', 'energy-gpu'),
    ]
    for (id, name, event_type) in rapl_sources:
        try:
            yield RaplSource(id, name, RaplHandle(event_type))
        except MeasureError:
            pass # Event is not available on this machine.

    # MCP sources
    print("Discovering MCP.")
    for device_id in range(5):
        try:
            device = McpDevice(f'/dev/ttyACM{device_id}')
        except MeasureError:
            continue # This MCP is not connected.
        for channel in range(2):
            yield McpSource(
                f'mcp{device_id}ch{channel}',
                f'MCP {device_id}, channel {channel}',
                McpHandle(device, channel),
            )

    # NVML sources
    print("Discovering NVML.")
    for gpu_index in range(10):
        try:
            handle = NvmlHandle(gpu_index)
        except MeasureError:
            continue # This GPU doesn't exist.
        yield NvmlSource(f'nvml{gpu_index}', f'NVML, external Nvidia GPU {gpu_index}', handle)


sources = list(discover_sources())
if len(sources) == 0:
    print(f'No sources available. Maybe you want to run this as sudo or adjust perf_event levels?')
    exit(0)
else:
    print(f'Available sources: {sources}')

def tick():
    for source in sources:
        source.tick()

def monitor():
    tick_repeatedly(short_term_resolution, tick)
