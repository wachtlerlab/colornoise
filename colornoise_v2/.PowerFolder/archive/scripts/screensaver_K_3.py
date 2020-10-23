#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python version 3.5.2

"""
For screen protection, this program can refresh a full-screen and colored mosaic pattern every 3 seconds.
New feature: support 10-bit color depth

"""

import numpy as np
import time
from psychopy import visual, core, monitors
from psychopy.hardware import keyboard
import sys
sys.path.insert(0, './scripts')
# from ..scripts.colorpalette_plus import ColorPicker


# from pypixxlib.viewpixx import VIEWPixx, _libdpx
# my_device = VIEWPixx()
# my_device.setVideoMode('M16') # Set the right video mode
# my_device.updateRegisterCache() # Update the device

def run_scrsaver(depthBits):
    mon = monitors.Monitor(name='VIEWPixx LITE', width=38, distance=57)
    mon.setSizePix((1920, 1200))
    mon.save()  # if the monitor info is not saved

    win = visual.Window(fullscr=True, mouseVisible=False, bpc=(depthBits, depthBits, depthBits), depthBits=depthBits,
                        monitor=mon)
    kb = keyboard.Keyboard()

    if depthBits == 8:
        colorSpace = 'rgb255'
    elif depthBits == 10:
        colorSpace = 'rgb'
    else:
        raise ValueError("Invalid color depth!")

    while True:
        num = np.random.randint(5, high=10)
        rect = visual.ElementArrayStim(win, units='norm', nElements=num ** 2, elementMask=None, elementTex=None,
                                       sizes=(2 / num, 2 / num), colorSpace=colorSpace)
        rect.xys = [(x, y) for x in np.linspace(-1, 1, num, endpoint=False) + 1 / num for y in
                    np.linspace(-1, 1, num, endpoint=False) + 1 / num]

        rect.colors = [ColorPicker(depthBits=depthBits, unit='deg').newcolor(x)[1] for x in
                       np.random.randint(0, high=360, size=num ** 2)]
        rect.draw()
        win.mouseVisible = False
        win.flip()

        kb.clock.reset()
        if kb.getKeys():  # press any key to quit
            core.quit()
        else:
            time.sleep(3)  # change every 3 sec

if __name__ == '__main__':
    run_scrsaver(int(sys.argv[1]))

"""example: execute the program with command"""
# python3.7 screensaver 8
