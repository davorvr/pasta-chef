## PASTA Chef

This is a repository which contains Python code which conducts an experiment with the PASTA platform, serving fresh *.pasta* files. For more information, see the paper "Repurposing a digital kitchen scale for neuroscience research: a complete hardware and software cookbook".

#### Links to paper:

* Insert URL

----

#### Dependencies (can be installed with pip):

    pyqtgraph
    numpy
    pyserial
    
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import numpy as np
import serial
import serial.tools.list_ports
import time
import threading
from collections import deque
import signal
import subprocess
from pathlib import Path
import json
