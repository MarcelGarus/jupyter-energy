import itertools
import time
from datetime import datetime, timedelta
from math import floor

# The server tracks both a short-term history of the energy consumption, so that
# you can immediately see the impact of individual actions.
# It also tracks a long-term history since the start of the server. This is used
# to make some inferences about long-term usage, like determining whether your
# notebook used renewable energy for its computations. Energy transmission
# operators only make these information available in a less detailed resolution,
# so this cannot be done with short-term data.

short_term_resolution: timedelta = timedelta(seconds=1)
long_term_resolution: timedelta = timedelta(minutes=15)


def only_date(dt: datetime) -> datetime:
    return datetime(dt.year, dt.month, dt.day)


def _start_time_floored_to_long_term_resolution() -> datetime:
    # The start time of the server, floored to the energy generation resolution.
    now = datetime.now()
    floored_minutes = 15 * floor(now.minute / 15)
    return datetime(now.year, now.month, now.day, now.hour, floored_minutes)


server_started: datetime = _start_time_floored_to_long_term_resolution()


def tick_repeatedly(delay: timedelta, callback) -> None:
    start_time = time.time()
    for i in itertools.count():
        time.sleep(max(0, start_time + i * delay.total_seconds() - time.time()))
        callback()
