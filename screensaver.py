#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python version 3.5.2

"""
For screen protection, this program can refresh a full-screen and colored mosaic pattern every 3 seconds.
It requires Psychopy package and colorpalette.py
"""

import numpy as np
import time
from psychopy import visual, core
from psychopy.hardware import keyboard
import colorpalette

win = visual.Window(fullscr=True, mouseVisible=False)
kb = keyboard.Keyboard()



while True:
    num = np.random.randint(5, high=10)
    rect = visual.ElementArrayStim(win, units='norm', nElements=num**2, elementMask=None, elementTex=None,
                                   sizes=(2 / num, 2 / num), colorSpace='rgb255')
    rect.xys = [(x, y) for x in np.linspace(-1, 1, num, endpoint=False) + 1 / num for y in
                np.linspace(-1, 1, num, endpoint=False) + 1 / num]

    rect.colors = [colorpalette.newcolor(x)[1] for x in np.random.randint(0, high=360, size=num**2)]
    rect.draw()
    win.mouseVisible = False
    win.flip()

    kb.clock.reset()
    if kb.getKeys():  # press any key to quit
        core.quit()
    else:
        time.sleep(3)  # change every 3 sec




