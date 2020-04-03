#!/usr/bin/python3

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
signal.signal(signal.SIGINT, signal.SIG_DFL)
font=QtGui.QFont()
font.setPixelSize(20)

# Path definitions
logdir = "data/"
Path(logdir).mkdir(exist_ok=True)
massfile = logdir+"mass.json"

# Loading the serial device
port = list(serial.tools.list_ports.grep("10c4:ea60"))
if not port:
	raise IOError("Serial device not found!")
else:
	dev = port[0][0]
baud = 115200

# Pyqtgraph options
pg.setConfigOptions(antialias=True)
pg.setConfigOption('background', (50, 50, 50))
pg.setConfigOption('foreground', (240, 240, 240))

def handler(msg_type, msg_log_context, msg_string):
    pass

QtCore.qInstallMessageHandler(handler)
app = QtGui.QApplication([])
view = pg.GraphicsView()
view.show()
l = pg.GraphicsLayout()
view.setCentralItem(l)
view.setWindowTitle('Load cell real-time plot')
view.resize(1600,400)

p = l.addPlot()
p.setDownsampling(mode='peak')
p.setClipToView(True)
p.showAxis('right', show=True)

p.setLabel('bottom', 'Time (s)')
p.getAxis('bottom').setScale(10**(-3))

p.setLabel('left', 'Measured mass (g)')

p.getAxis('bottom').setTickSpacing(1, 0.1)
p.getAxis('left').setTickSpacing(1000, 100)
p.getAxis('right').setTickSpacing(1000, 100)
p.getAxis('bottom').setTickSpacing(0.5, 0.1)
p.showGrid(y=True, x=True, alpha=0.2)

p.setXRange(-10000, 0)
p.setYRange(0, 5000)
p.setLimits(xMax=0)
curve = p.plot()
curve.setPen(pg.mkPen(color=(240, 240, 240), width=2))

data = deque([], 5000)
ptr = 0
timer = QtCore.QTime()

# Ask for test animal data
animalname = str(input("Animal name: "))
logname = logdir+animalname+".pasta"
mass = float(input("Animal mass: "))

ser = serial.Serial(dev,baud)

# This function grabs data from the serial device.
def update_ser():
    global data, ser, logname
    t = threading.currentThread()
    logfile = open(logname, "w")
    while getattr(t, "running", True):
        ser_in = None
        while ser_in is None:
            try:
                ser_in = float(ser.readline())
            except ValueError:
                pass
        time = timer.elapsed()
        logfile.write(str(time)+","+str(ser_in)+"\n")
        data.append({'x': time, 'y': ser_in})
    logfile.close()

# This function maps incoming data onto the real-time plot.
def update_plot():
    global x, y, p, data, curve
    data_temp = list(data)
    x = [item['x'] for item in data_temp]
    y = [item['y'] for item in data_temp]
    curve.setData(x=x, y=y)
    curve.setPos(-(timer.elapsed()), 0)

# This is the main function which calls the others.
def play_and_exit():
    time.sleep(0.2)
    logthread = threading.Thread(target=update_ser)
    logthread.running = True
    logthread.start()
    
    subprocess.call(["/usr/bin/aplay", "startlesnd.wav"])
    
    app.exit()
    
    logthread.running = False
    logthread.join()

# Sleeping for 0.5 seconds seems to help flush the serial buffer.
# See more here: https://github.com/pyserial/pyserial/issues/298
time.sleep(0.5)

timer.start()

# Call the update_plot function every 10 ms
timer_plot = pg.QtCore.QTimer()
timer_plot.timeout.connect(update_plot)
timer_plot.start(10)

# Start the main thread
testthread = threading.Thread(target=play_and_exit)
testthread.start()

app.exec_()

testthread.join()
timer_plot.stop()
ser.close()

# Correct the offset from baseline
with open(logfile, "r") as f:
    linesum = 0
    linenr = 0
    for line in f:
        parsedline = line.rstrip().split(",")
        linesum += float(parsedline[1])
        linenr += 1
    avg = linesum/linenr
    f.seek(0)
    with open(logfile+".tmp", "w") as tmpf:
        for line in f:
            parsedline = line.rstrip().split(",")
            #parsedline[1] = round(float(parsedline[1])-avg, 4)
            parsedline[1] = float(parsedline[1])-avg
            tmpf.write(str(parsedline[0])+","+str(parsedline[1])+"\n")

os.remove(logfile)
os.rename(logfile+".tmp", logfile)

# Add this animal's mass to the mass.json file
masses = {}

if Path(massfile).exists():
    if Path(massfile).stat().st_size:
        with open(massfile, "r") as mf:
            masses = json.load(mf)

with open(massfile, "w") as mf:
    masses.update({animalname : float(mass)})
    json.dump(masses, mf)

# Done
print("Test finished.")
