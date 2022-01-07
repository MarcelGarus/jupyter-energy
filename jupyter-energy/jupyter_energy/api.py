import json
import time
from concurrent.futures import ThreadPoolExecutor

import requests as req
from jupyter_server.base.handlers import APIHandler
from tornado import web


def fetch_energy_metrics():
    return json.loads(req.get('http://localhost:35396').text)


class ApiHandler(APIHandler):
    executor = ThreadPoolExecutor(max_workers=5)
    initial_metrics = fetch_energy_metrics()
    previous_metrics = initial_metrics
    current_metrics = initial_metrics
    previous_time = time.time()
    current_time = previous_time

    @web.authenticated
    async def get(self):
        """
        Calculate and return current energy metrics
        """
        now = time.time()
        if now - self.current_time > 0.1:
            self.previous_metrics = self.current_metrics
            self.current_metrics = fetch_energy_metrics()
            self.previous_time = self.current_time
            self.current_time = now

        delta = self.current_time - self.previous_time
        response = {}
        for id, source in self.current_metrics.items():
            initial_source = self.initial_metrics[id]
            previous_source = self.previous_metrics[id]
            response[id] = {
                'name': source['name'],
                'joules': source['joules'] - initial_source['joules'],
                'watts': 0 if delta == 0 else (source['joules'] - previous_source['joules']) / delta
                # 'timeline': ...
            }
        print(f'Response: {response}')
        self.write(json.dumps(response))
