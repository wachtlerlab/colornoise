# !/usr/bin/env python3.7
# -*- coding: utf-8 -*-
""" 
Created on 21.08.20

@author yannansu
"""

"""
A demo program shows color circle and allows customized contrast values. 
"""

from colorpalette import ColorPicker
import numpy as np
from psychopy import visual, misc, event, core
import argparse


def show_colorcircle(subject, contrast, depthBits, numStim):
    if contrast is None:
        contrast = 0.15
    if depthBits is None:
        depthBits = 10
    if numStim is None:
        numStim = 16

    theta = np.linspace(0, 2 * np.pi, numStim, endpoint=False)

    cp = ColorPicker(c=contrast, sscale=2.6, unit='rad', depthBits=depthBits, subject=None)
    Msml = []
    Mrgb = []
    for t in theta:
        sml, rgb = cp.newcolor(theta=t)
        Msml.append(sml)
        Mrgb.append(rgb)

    sub_cp = ColorPicker(c=contrast, sscale=2.6, unit='rad', depthBits=depthBits, subject=subject)
    sub_Msml = []
    sub_Mrgb = []
    for t in theta:
        sml, rgb = sub_cp.newcolor(theta=t)
        sub_Msml.append(sml)
        sub_Mrgb.append(rgb)

    winM = visual.Window(fullscr=True, allowGUI=True, bpc=(cp.depthBits, cp.depthBits, cp.depthBits),
                         depthBits=cp.depthBits, colorSpace=cp.colorSpace, color=cp.sml2rgb(cp.center()))

    rectsize = 0.2 * winM.size[0] * 2 / numStim
    radius = 0.1 * winM.size[0]
    alphas = np.linspace(0, 360, numStim, endpoint=False)

    rect = visual.Rect(win=winM,
                       units="pix",
                       width=int(rectsize), height=int(rectsize))

    winM.flip()
    for t in range(50):
        for wait_keys in event.waitKeys():
            if wait_keys == 'left':
                for i_rect in range(numStim):
                    rect.fillColorSpace = cp.colorSpace
                    rect.lineColorSpace = cp.colorSpace
                    rect.fillColor = Mrgb[i_rect]
                    rect.lineColor = Mrgb[i_rect]
                    rect.pos = misc.pol2cart(alphas[i_rect], radius)
                    rect.draw()
                winM.flip()
            elif wait_keys == 'right':
                sub_rect = rect
                for i_rect in range(numStim):
                    sub_rect.fillColorSpace = sub_cp.colorSpace
                    sub_rect.lineColorSpace = sub_cp.colorSpace
                    sub_rect.fillColor = sub_Mrgb[i_rect]
                    sub_rect.lineColor = sub_Mrgb[i_rect]
                    sub_rect.pos = misc.pol2cart(alphas[i_rect], radius)
                    sub_rect.draw()
                    text = visual.TextStim(winM, text=subject, pos=[0.3, -0.5], height=0.05, color='black')
                    text.draw()
                winM.flip()
            elif wait_keys == 'escape':
                core.quit()

# show_colorcircle(subject='ysu', contrast=0.145, depthBits=8, numStim=16)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--subject', type=str)
    parser.add_argument('--contrast', type=float)
    parser.add_argument('--depthBits', type=int)
    parser.add_argument('--numStim', type=int)

    args = parser.parse_args()
    show_colorcircle(args.subject, args.contrast, args.depthBits, args.numStim)

