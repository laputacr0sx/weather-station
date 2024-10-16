import os

# Import specific functions or classes from submodules
from .assest.font import cubic_font

# Define package-level variables
__version__ = "0.0.1"

# Control what is accessible when using 'from mypackage import *'
__all__ = ["cubic_font"]


EPD_WIDTH = 800
EPD_HEIGHT = 480
HKO_URL = "https://data.weather.gov.hk/weatherAPI/opendata/weather.php"
LINE_DIR = os.path.join(os.path.dirname(__file__), "assest", "img", "out")
PIC_DIR = os.path.join(os.path.dirname(__file__), "assest", "img", "pic")
ASSEST_DIR = os.path.join(os.path.dirname(__file__), "assest")
