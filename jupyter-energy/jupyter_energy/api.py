from concurrent.futures import ThreadPoolExecutor

import requests as req
from jupyter_server.base.handlers import APIHandler
from tornado import web


class ApiHandler(APIHandler):
    executor = ThreadPoolExecutor(max_workers=5)

    @web.authenticated
    async def get(self):
        """
        Calculate and return current energy metrics
        """
        config = self.settings["jupyter_energy_config"]
        # print(f"Config: {config}")
        response = req.get('http://localhost:35396')
        print(response.text.strip())
        self.write(response.text)
        # self.write(json.dumps(metrics))
