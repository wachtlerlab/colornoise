#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python version 3.5.2

"""
For screen protection, this program can refresh a full-screen and colored mosaic pattern every 3 seconds.
It requires Psychopy package and colorpalette10bit.py

dependencies for pypixxlib:
"""

import numpy as np
import time
from psychopy import visual, core, monitors
from psychopy.hardware import keyboard
import colorpalette10bit
from pypixxlib.viewpixx import VIEWPixx, _libdpx 

my_device = VIEWPixx()
my_device.setVideoMode('M16') # Set the right video mode
my_device.updateRegisterCache() # Update the device
_libdpx.DPxOpen()
_libdpx.DPxDisableDinStabilize()
_libdpx.DPxEnableDinDebounce()
_libdpx.DPxEnableDinLogTimetags()
_libdpx.DPxEnableDinLogEvents()
_libdpx.DPxSetDinDataDir(int("00FF0000", 16))
_libdpx.DPxSetDinBuff(int("C00000", 16), int("400000", 16))
_libdpx.DPxSetDinDataOut(int("000000", 16))
_libdpx.DPxUpdateRegCache()

mon = monitors.Monitor('VIEWPixx LITE')
# mon.setDistance(114)#further away than normal?
# win = visual.Window(size=[1024,768], monitor=mon)

win = visual.Window(fullscr=True, mouseVisible=False, bpc=(10, 10, 10), depthBits=10, monitor=mon)
kb = keyboard.Keyboard()



while True:
    num = np.random.randint(5, high=10)
    rect = visual.ElementArrayStim(win, units='norm', nElements=num**2, elementMask=None, elementTex=None,
                                   sizes=(2 / num, 2 / num), colorSpace='rgb')
    rect.xys = [(x, y) for x in np.linspace(-1, 1, num, endpoint=False) + 1 / num for y in
                np.linspace(-1, 1, num, endpoint=False) + 1 / num]

    rect.colors = [colorpalette10bit.newcolor(x)[1] for x in np.random.randint(0, high=360, size=num ** 2)]
    rect.draw()
    win.mouseVisible = False
    win.flip()

    kb.clock.reset()
    if kb.getKeys():  # press any key to quit
        core.quit()
    else:
        time.sleep(3)  # change every 3 sec




