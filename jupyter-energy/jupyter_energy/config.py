import os

from traitlets import Bool, Dict, Float, Int, List, TraitType, Union, default
from traitlets.config import Configurable


class ResourceUseDisplay(Configurable):
    """
    Holds server-side configuration for jupyter-energy
    """
