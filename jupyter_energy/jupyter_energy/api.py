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

    @web.authenticated
    async def get(self):
        """
        Calculate and return current energy metrics
        """
        metrics = fetch_energy_metrics()
        response = {
            'usage': {},
            'generation': {}
        }
        for id, source in metrics['usage'].items():
            initial_source = self.initial_metrics['usage'][id]
            response['usage'][id] = {
                'name': source['name'],
                'joules': source['joules'] - initial_source['joules'],
                'watts': source['watts'],
                'wattsOverTime': source['wattsOverTime'],  # TODO: possibly shorten it
                'longTermJoules': source['longTermJoules'],
            }
        response['generation'] = metrics['generation']
        print(f'Response: {response}')
        self.write(json.dumps(response))
