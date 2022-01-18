import itertools
import json
import time
from datetime import datetime

import requests

from server.utils import *


class Info:
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
infos_by_day = {}


def _get_info():
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
        output.append(Info(
            storage, renewable, non_renewable, unknown))
    return output


def tick():
    today = datetime.now().strftime('%Y-%m-%d')
    list_of_generation_info = _get_info()
    infos_by_day[today] = list_of_generation_info


def monitor():
    start_time = time.time()
    interval = 60 * 15
    for i in itertools.count():
        if not running:
            return
        time.sleep(max(0, start_time + i*interval - time.time()))
        tick()
