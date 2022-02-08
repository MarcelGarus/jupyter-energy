import json
from datetime import datetime, timedelta
from typing import List

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


def _get_info(day: datetime):
    # Returns a list of `Info`s, one for every long_term_resolution since the day started.

    url = 'https://transparency.entsoe.eu/generation/r2/actualGenerationPerProductionType/show?name=&defaultValue=false&viewType=GRAPH&areaType=CTY&atch=false&datepicker-day-offset-select-dv-date-from_input=D&dateTime.dateTime=16.01.2022 00:00|CET|DAYTIMERANGE&dateTime.endDateTime=16.01.2022 00:00|CET|DAYTIMERANGE&area.values=CTY|10Y1001A1001A83F!CTY|10Y1001A1001A83F&productionType.values=B01&productionType.values=B02&productionType.values=B03&productionType.values=B04&productionType.values=B05&productionType.values=B06&productionType.values=B07&productionType.values=B08&productionType.values=B09&productionType.values=B10&productionType.values=B11&productionType.values=B12&productionType.values=B13&productionType.values=B14&productionType.values=B20&productionType.values=B15&productionType.values=B16&productionType.values=B17&productionType.values=B18&productionType.values=B19&dateTime.timezone=CET_CEST&dateTime.timezone_input=CET (UTC+1) / CEST (UTC+2)&_=1642498848217'
    r = requests.get(url)
    print(r)

    content = str(r.content)
    chart = json.loads(content.split('var chart = ')[1].split(';')[0])

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
    # print(f'Renewable: {renewable_keys}')
    # print(f'Non-Renewable: {non_renewable_keys}')
    # print(f'From Storage: {storage_keys}')
    # print(f'Unknown: {unknown_keys}')

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


# A map from days to a list of `Info`s reported for that day.
_infos_by_day = {}

# A list that contains an Info for every long_term_resolution since the server
# started.
infos: List[datetime] = []


def tick():
    global infos

    today = only_date(datetime.now())
    day_info = _get_info(today)
    _infos_by_day[today.isoformat()] = day_info

    infos = []
    day = only_date(server_started)
    while day <= today:
        day_infos = _infos_by_day[day.isoformat()]
        if day == only_date(server_started):
            to_trim = round((server_started - only_date(server_started)) /
                            long_term_resolution)
            day_infos = day_infos[to_trim:]
        infos.extend(day_infos)
        day += timedelta(days=1)


def monitor():
    tick_repeatedly(long_term_resolution, tick)
