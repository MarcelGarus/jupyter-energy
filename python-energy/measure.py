#!/usr/bin/env python

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

HERE = osp.abspath(osp.dirname(__file__))


class MeasureError(Exception):
    def __init__(self, type, arg):
        super().__init__(f'{type}: {arg}')


def assert_valid(event_type, obj):
    def fail(msg): raise MeasureError(event_type, msg)
    if obj >= 0:
        return obj
    if obj == -1:
        raise fail('Event is not supported.')
    if obj == -2:
        raise fail('Unknown unit. We can only handle joules.')
    if obj == -3:
        raise fail('Cannot access power measurement.')
    if obj == -4:
        raise fail('Unexpected event config file.')
    if obj == -5:
        raise fail('Missing permissions. Try running this as sudo.')
    if obj == -6:
        raise fail('Syscall failed for unknown reason.')
    if obj == -7:
        raise fail('Couldn\'t read consumed energy.')
    if obj == -8:
        raise fail('Used an invalid handle.')
    raise fail('Shared library returned unknown error code.')


class OngoingEnergyRecording:
    dll = ctypes.CDLL(f'{HERE}/measure.so')

    def __init__(self, event_type: str):
        self.event_type = event_type
        self.handle = -1
        start_recording_energy = self.dll.start_recording_energy
        start_recording_energy.restype = ctypes.c_long
        self.handle = self.assert_valid(
            start_recording_energy(event_type.encode('utf-8')))

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

class Source:
    def __init__(self, id: str, name: str, recording: OngoingEnergyRecording):
        self.id = id
        self.name = name
        self.recording = recording
        self.joules = 0
        self.watts = 0
        self.wattsOverTime = deque([])
        self.joulesPerQuarterHour = {}  # map from days to lists with joules per 15 minutes


sources = [
    Source('all', 'all', record_energy('energy-pkg')),
    Source('cpu', 'CPU', record_energy('energy-cores')),
    Source('ram', 'RAM', record_energy('energy-ram')),
    Source('gpu', 'Integrated GPU', record_energy('energy-gpu')),
]
running = True


# Is called every second
def energy_usage_tick():
    for source in sources:
        joules = source.recording.used_joules()
        source.watts = joules - source.joules
        source.joules = joules

        source.wattsOverTime.append(source.watts)
        if len(source.wattsOverTime) > 100:
            source.wattsOverTime.popleft()

        now = datetime.now()
        beginning_of_day = datetime(now.year, now.month, now.day, 0, 0, 0)
        quarter_hours_since_beginning_of_day = ceil((
            now - beginning_of_day).total_seconds() / (60 * 15))
        day = beginning_of_day.strftime('%Y-%m-%d')
        if day not in source.joulesPerQuarterHour:
            source.joulesPerQuarterHour[day] = []
        while len(source.joulesPerQuarterHour[day]) < quarter_hours_since_beginning_of_day - 1:
            source.joulesPerQuarterHour[day].append(0)
        if len(source.joulesPerQuarterHour[day]) < quarter_hours_since_beginning_of_day:
            source.joulesPerQuarterHour[day].append(source.watts)
        else:
            source.joulesPerQuarterHour[day][quarter_hours_since_beginning_of_day - 1] += source.watts


def monitor_energy_usage():
    start_time = time.time()
    interval = 1
    for i in itertools.count():
        if not running:
            return
        time.sleep(max(0, start_time + i*interval - time.time()))
        energy_usage_tick()


class GenerationInfo:
    def __init__(self, storage: int, renewable: int, non_renewable: int, unknown: int):
        self.storage = storage
        self.renewable = renewable
        self.non_renewable = non_renewable
        self.unknown = unknown

    def to_json(self):
        return {
            'storage': self.storage,
            'renewable': self.renewable,
            'nonRenewable': self.non_renewable,
            'unknown': self.unknown,
        }


# A map from ISO-8859-1 date notation to lists that contain a renewable for
# every 15 minutes.
generation_infos_by_day = {}


def get_energy_generation_info():
    # Returns a list of `GenerationInfo`, one for every quarter hour since the day started.

    r = requests.get(
        'https://transparency.entsoe.eu/generation/r2/actualGenerationPerProductionType/show?name=&defaultValue=false&viewType=GRAPH&areaType=CTY&atch=false&datepicker-day-offset-select-dv-date-from_input=D&dateTime.dateTime=16.01.2022 00:00|CET|DAYTIMERANGE&dateTime.endDateTime=16.01.2022 00:00|CET|DAYTIMERANGE&area.values=CTY|10Y1001A1001A83F!CTY|10Y1001A1001A83F&productionType.values=B01&productionType.values=B02&productionType.values=B03&productionType.values=B04&productionType.values=B05&productionType.values=B06&productionType.values=B07&productionType.values=B08&productionType.values=B09&productionType.values=B10&productionType.values=B11&productionType.values=B12&productionType.values=B13&productionType.values=B14&productionType.values=B20&productionType.values=B15&productionType.values=B16&productionType.values=B17&productionType.values=B18&productionType.values=B19&dateTime.timezone=CET_CEST&dateTime.timezone_input=CET (UTC+1) / CEST (UTC+2)&_=1642498848217',
        # headers={
        #     'Referer': 'https://transparency.entsoe.eu/generation/r2/actualGenerationPerProductionType/show?name=&defaultValue=false&viewType=GRAPH&areaType=CTY&atch=false&datepicker-day-offset-select-dv-date-from_input=D&dateTime.dateTime=16.01.2022+00:00|CET|DAYTIMERANGE&dateTime.endDateTime=16.01.2022+00:00|CET|DAYTIMERANGE&area.values=CTY|10Y1001A1001A83F!CTY|10Y1001A1001A83F&productionType.values=B01&productionType.values=B02&productionType.values=B03&productionType.values=B04&productionType.values=B05&productionType.values=B06&productionType.values=B07&productionType.values=B08&productionType.values=B09&productionType.values=B10&productionType.values=B11&productionType.values=B12&productionType.values=B13&productionType.values=B14&productionType.values=B20&productionType.values=B15&productionType.values=B16&productionType.values=B17&productionType.values=B18&productionType.values=B19&dateTime.timezone=CET_CEST&dateTime.timezone_input=CET+(UTC+1)+/+CEST+(UTC+2)',
        #     'Content-Type': 'application/json;charset=UTF-8',
        #     'Host': 'transparency.entsoe.eu',
        # }
    )
    print(r)

    content = str(r.content)
    chart = json.loads(content.split('var chart = ')[1].split(';')[0])
    # print(chart)

    keys = chart['chartKeys']
    renewable_keys, non_renewable_keys, storage_keys, unknown_keys = set(), set(), set(), set()
    for key in keys:
        name: str = (chart['graphDesign'][key]['title']).lower()
        if 'consumption' in name:
            continue

        def matches_keywords(keywords):
            return any(map(lambda it: it in name, keywords))

        if matches_keywords(['reservoir', 'storage']):
            storage_keys.add(key)
        elif matches_keywords(['biomass', 'geothermal', 'hydro', 'renewable', 'solar', 'waste', 'wind']):
            renewable_keys.add(key)
        elif matches_keywords(['fossil', 'nuclear']):
            non_renewable_keys.add(key)
        else:
            unknown_keys.add(key)
    print(f'Renewable: {renewable_keys}')
    print(f'Non-Renewable: {non_renewable_keys}')
    print(f'From Storage: {storage_keys}')
    print(f'Unknown: {unknown_keys}')

    assert(chart['chartDesign']['xAxisTitle'] == 'Time [Hours]')

    output = []
    for data in chart['chartData']:
        time = data['cat']
        storage, renewable, non_renewable, unknown = 0, 0, 0, 0
        for key in keys:
            energy = int(data[key])
            if key in storage_keys:
                storage += energy
            if key in renewable_keys:
                renewable += energy
            if key in non_renewable_keys:
                non_renewable += energy
            if key in unknown_keys:
                unknown += energy
        output.append(GenerationInfo(
            storage, renewable, non_renewable, unknown))
    return output


def energy_generation_tick():
    today = datetime.now().strftime('%Y-%m-%d')
    list_of_generation_info = get_energy_generation_info()
    generation_infos_by_day[today] = list_of_generation_info


def monitor_energy_generation():
    start_time = time.time()
    interval = 60 * 15
    for i in itertools.count():
        if not running:
            return
        time.sleep(max(0, start_time + i*interval - time.time()))
        energy_generation_tick()


class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/json')
        self.end_headers()
        response = {}
        for source in sources:
            response[source.id] = {
                'name': source.name,
                'joules': source.joules,
                'watts': source.watts,
                'wattsOverTime': list(source.wattsOverTime),
                'joulesPerQuarterHour': source.joulesPerQuarterHour,
            }
        response['generation'] = {}
        for day in generation_infos_by_day.keys():
            infos = generation_infos_by_day[day]
            response['generation'][day] = {
                'storage': list(map(lambda info: info.storage, infos)),
                'renewable': list(map(lambda info: info.renewable, infos)),
                'nonRenewable': list(map(lambda info: info.non_renewable, infos)),
                'unknown': list(map(lambda info: info.unknown, infos)),
            }
        self.wfile.write(bytes(json.dumps(response), 'utf-8'))
        self.wfile.write(bytes('\n', 'utf-8'))


if __name__ == '__main__':
    Thread(target=monitor_energy_usage, args=()).start()
    Thread(target=monitor_energy_generation, args=()).start()

    web_server = HTTPServer(('localhost', 35396), MyServer)
    print('Server started http://%s:%s' % ('localhost', 35396))

    try:
        web_server.serve_forever()
    except KeyboardInterrupt:
        pass

    web_server.server_close()
    running = False
    print('Server stopped.')
