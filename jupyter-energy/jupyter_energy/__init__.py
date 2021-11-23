import json
import os.path as osp

from jupyter_server.utils import url_path_join
from tornado import ioloop

from jupyter_energy.api import ApiHandler
from jupyter_energy.config import ResourceUseDisplay
from jupyter_energy.metrics import PSUtilMetricsLoader
from jupyter_energy.prometheus import PrometheusHandler

HERE = osp.abspath(osp.dirname(__file__))

with open(osp.join(HERE, "labextension", "package.json")) as fid:
    data = json.load(fid)


def _jupyter_labextension_paths():
    return [{"src": "labextension", "dest": data["name"]}]


def _jupyter_server_extension_points():
    """
    Set up the server extension for collecting metrics
    """
    return [{"module": "jupyter_energy"}]


def _jupyter_nbextension_paths():
    """
    Set up the notebook extension for displaying metrics
    """
    return [
        {
            "section": "notebook",
            "dest": "jupyter_energy",
            "src": "static",
            "require": "jupyter_energy/main",
        }
    ]


def _load_jupyter_server_extension(server_app):
    """
    Called during notebook start
    """
    resuseconfig = ResourceUseDisplay(parent=server_app)
    server_app.web_app.settings["jupyter_energy_config"] = resuseconfig
    base_url = server_app.web_app.settings["base_url"]

    server_app.web_app.add_handlers(
        ".*", [(url_path_join(base_url, "/api/metrics/v1"), ApiHandler)]
    )

    callback = ioloop.PeriodicCallback(
        PrometheusHandler(PSUtilMetricsLoader(server_app)), 1000
    )
    callback.start()


load_jupyter_server_extension = _load_jupyter_server_extension
