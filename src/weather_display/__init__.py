import os

# Import specific functions or classes from submodules
from .assest.font import cubic_font

# Define package-level variables
__version__ = "0.0.1"

# Control what is accessible when using 'from mypackage import *'
__all__ = ["cubic_font"]


LINE_DIR = os.path.join(os.path.dirname(__file__), "assest", "img", "out")
PIC_DIR = os.path.join(os.path.dirname(__file__), "assest", "img", "pic")
ASSEST_DIR = os.path.join(os.path.dirname(__file__), "assest")
