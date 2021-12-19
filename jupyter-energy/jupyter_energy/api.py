import json
import os.path as osp
import subprocess
from concurrent.futures import ThreadPoolExecutor

import psutil
import requests as req
from jupyter_server.base.handlers import APIHandler
from tornado import web
from tornado.concurrent import run_on_executor

from .measure import OngoingEnergyRecording, record_energy

try:
    # Traitlets >= 4.3.3
    from traitlets import Callable
except ImportError:
    from .utils import Callable


HERE = osp.abspath(osp.dirname(__file__))


class ApiHandler(APIHandler):
    executor = ThreadPoolExecutor(max_workers=5)

    def prepare(self):
        print("Preparing API handler.")
        # self.process = subprocess.Popen(["sudo", "-i", "python3", f"/home/marcel/projects/jupyter-energy/python-energy/measure.py"],
        #                                 stdout=subprocess.PIPE, stdin=subprocess.PIPE, shell=True)
        # print(f"Process {self.process}")
        # out_value = self.process.communicate()
        # print(f"Communicating with process {out_value}")
        return super().prepare()

    @web.authenticated
    async def get(self):
        """
        Calculate and return current energy metrics
        """
        config = self.settings["jupyter_energy_config"]
        print(f"Config: {config}")
        response = req.get('http://localhost:35396')
        print(response)
        print(response.text)
        self.write(response.text)

        # self.write(json.dumps(metrics))

    # @run_on_executor
    # def _get_cpu_percent(self, all_processes):
    #     def get_cpu_percent(p):
    #         try:
    #             return p.cpu_percent(interval=0.05)
    #         # Avoid littering logs with stack traces complaining
    #         # about dead processes having no CPU usage
    #         except:
    #             return 0

    #     return sum([get_cpu_percent(p) for p in all_processes])
