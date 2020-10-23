#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# python version 3.5.2
"""
This module runs color tests on the 10-bit display -- to test if the color code works.

"""

from psychopy import visual, event, core, monitors
import numpy as np
import sys
sys.path.insert(0, './scripts')
from colorpalette_plus import ColorPicker


def test1(bit):
    """
    Abandoned!!!

    for test1(8), color should change every 3 steps;
    for test1(10), color should change every step
    """
    # visual.backends.getBackend(win=self,
    #                     bpc=bpc,
    #                     depthBits=depthBits,
    #                     stencilBits=stencilBits,
    #                     *args, **kwargs)

    # bpc:
    #   array_like or int Bits per color for the back buffer.
    #   Valid values depend on the output color depth of the display.
    #   By default, it is assumed the display has 8 - bits per color(8, 8, 8)
    # depthBits:
    #   int, Back buffer depth bits. Default is 8.
    # stencilBits:
    #   int Back buffer stencil bits. Default is 8.

    rlist = np.linspace(0.5, 0.6, 100, endpoint=True)  # each step is 0.001 in [0, 1] scale;
    # so we expect color changes every step for 10-bit (1/1023 = 0.0009), but changes every 3 steps for 8-bit (1/255 = 0.0039)

    glist = np.linspace(0.4, 0.5, 100, endpoint=True)
    blist = np.linspace(0.8, 0.9, 100, endpoint=True)
    rgb = np.squeeze(np.dstack((rlist, glist, blist)))

    colorspace = None
    Crgb = ColorPicker().Crgb / 255

    if bit == 10:
        colorspace = 'rgb'
        rgb = rgb * 2 - 1  # converted to [-1, 1]
        Crgb = Crgb * 2 - 1
    elif bit == 8:
        colorspace = 'rgb255'
        rgb = rgb * 255  # converted to [0, 255]
        Crgb = Crgb * 255

    win = visual.Window([600, 600], color=list(Crgb), colorSpace=colorspace, bpc=(bit, bit, bit), depthBits=bit)
    text = visual.TextStim(win, text=str(bit) + ' bit', pos=[-0.7, 0.95], height=0.03)
    text.draw()

    num = 40

    selrgb = rgb[0:num]
    boundary = 0.8

    colorbar = visual.ElementArrayStim(win, units='norm', nElements=num, elementMask=None, elementTex=None,
                                       sizes=(boundary * 2 / num, boundary), colorSpace=colorspace)
    colorbar.xys = [(x, 0) for x in np.linspace(-boundary, boundary, num, endpoint=False) + boundary / num]

    colorbar.colors = selrgb

    colorbar.draw()

    win.flip()
    if event.waitKeys():
        win.close()
        return


"""
test2: compare colors coded with difference of less than 1 (in 8-bit color space) in R/G/B gun
"""


def test2():
    """
    Abandoned!!!
    """
    _, color = ColorPicker().newcolor(theta=90, unit='deg')

    newR = np.array([color[0] - 1.0, color[1], color[2]])  # should be visible on 8-bit display
    newG = np.array([color[0], color[1] + 1.0, color[2]])
    newB = np.array([color[0], color[1], color[2] + 1.0])

    testR = np.array([color[0] - 0.5, color[1], color[2]])  # should be only visible on 10-bit display
    testG = np.array([color[0], color[1] + 0.5, color[2]])
    testB = np.array([color[0], color[1], color[2] + 0.5])

    allcolor = np.stack([newR, newG, newB, testR, testG, testB])
    convertrgb = allcolor / 255 * 2 - 1  # convert from [0, 255] to [-1, 1]
    convert1023 = allcolor / 255 * 1023

    Crgb = list(ColorPicker().Crgb / 255 * 2 - 1)

    win = visual.Window([1000, 1000], color=Crgb, colorSpace='rgb')  # need bpc=(bit, bit, bit), depthBits=bit?
    for idx in range(3):
        colorRect = visual.Rect(win, width=0.2, height=0.2, pos=[-0.6, (idx - 1) * 0.5], fillColor=color / 255 * 2 - 1,
                                lineColor=Crgb)
        colorText = visual.TextStim(win, text=str(np.round(color, decimals=2)), pos=[-0.6, (idx - 1) * 0.5 + 0.2],
                                    height=0.05)
        colorText1023 = visual.TextStim(win, text=str(np.round(color / 255 * 1023, decimals=2)),
                                        pos=[-0.6, (idx - 1) * 0.5 + 0.3], height=0.05)

        newRect = visual.Rect(win, width=0.2, height=0.2, pos=[0.6, (idx - 1) * 0.5], fillColor=convertrgb[idx],
                              lineColor=Crgb)
        newText = visual.TextStim(win, text=str(np.round(allcolor[idx], decimals=2)), pos=[0.6, (idx - 1) * 0.5 + 0.2],
                                  height=0.05)
        newText1023 = visual.TextStim(win, text=str(np.round(convert1023[idx], decimals=2)),
                                      pos=[0.6, (idx - 1) * 0.5 + 0.3],
                                      height=0.05)

        testRect = visual.Rect(win, width=0.2, height=0.2, pos=[0, (idx - 1) * 0.5], fillColor=convertrgb[idx + 3],
                               lineColor=Crgb)
        testText = visual.TextStim(win, text=str(np.round(allcolor[idx + 3], decimals=2)),
                                   pos=[0, (idx - 1) * 0.5 + 0.2],
                                   height=0.05)
        testText1023 = visual.TextStim(win, text=str(np.round(convert1023[idx + 3], decimals=2)),
                                       pos=[0, (idx - 1) * 0.5 + 0.3],
                                       height=0.05)

        colorRect.draw()
        colorText.draw()
        colorText1023.draw()

        newRect.draw()
        newText.draw()
        newText1023.draw()

        testRect.draw()
        testText.draw()
        testText1023.draw()

    win.flip()
    if event.waitKeys():
        win.close()
        return


"""
test 3: same as test 2, but remove the gaps between patches
"""


def test3():
    """
    Abandoned!!!
    """
    # _, color = ColorPicker(unit='deg').newcolor(theta=90)
    color = ColorPicker().Crgb

    newR = np.array([color[0] - 1.0, color[1], color[2]])  # should be visible on 8-bit display
    newG = np.array([color[0], color[1] + 1.0, color[2]])
    newB = np.array([color[0], color[1], color[2] + 1.0])

    testR = np.array([color[0] - 0.5, color[1], color[2]])  # should be only visible on 10-bit display
    testG = np.array([color[0], color[1] + 0.5, color[2]])
    testB = np.array([color[0], color[1], color[2] + 0.5])

    allcolor = np.stack([newR, newG, newB, testR, testG, testB])
    convertrgb = allcolor / 255 * 2 - 1  # convert from [0, 255] to [-1, 1]
    convert1023 = allcolor / 255 * 1023

    Crgb = list(ColorPicker().Crgb / 255 * 2 - 1)

    win = visual.Window(fullscr=True, color=Crgb, colorSpace='rgb',
                        unit='pix')  # need bpc=(bit, bit, bit), depthBits=bit?
    size = 0.3

    for idx in range(3):
        colorRect = visual.Rect(win, width=size, height=size, pos=[-0.3, (idx - 1) * 0.3],
                                fillColor=color / 255 * 2 - 1, lineColor=Crgb)

        newRect = visual.Rect(win, width=size, height=size, pos=[0.3, (idx - 1) * 0.3], fillColor=convertrgb[idx],
                              lineColor=Crgb)

        testRect = visual.Rect(win, width=size, height=size, pos=[0, (idx - 1) * 0.3], fillColor=convertrgb[idx + 3],
                               lineColor=Crgb)

        colorRect.draw()
        newRect.draw()
        testRect.draw()

    win.flip()
    if event.waitKeys():
        win.close()
        return


def test4():
    """
    Abandoned!!!
    Temporal changes of colors: should be only visible on 10-bit display
    """
    from psychopy.hardware import keyboard
    import time

    Crgb = ColorPicker().Crgb

    _, color = ColorPicker(unit='deg').newcolor(theta=90)

    testR = np.array([color[0] - 0.5, color[1], color[2]])  # should be only visible on 10-bit display
    testG = np.array([color[0], color[1] + 0.5, color[2]])
    testB = np.array([color[0], color[1], color[2] + 0.5])

    allcolor = np.stack([color, testR, testG, testB])

    kb = keyboard.Keyboard()

    win = visual.Window(unit='pix', size=[800, 800], allowGUI=True, fullscr=True, colorSpace="rgb255", color=Crgb)
    while True:
        nowcolor = allcolor[int(np.random.choice(4, 1, replace=False))]

        rect = visual.Rect(win, width=0.5, height=0.5, pos=[0, 0], fillColorSpace='rgb255', lineColorSpace='rgb255',
                           lineColor=list(Crgb))
        rect.fillColor = nowcolor

        text = visual.TextStim(win, text=str(nowcolor), pos=[0, -0.8], height=0.05)
        win.mouseVisible = False

        rect.draw()
        text.draw()
        win.flip()

        kb.clock.reset()
        if kb.getKeys():  # press any key to quit
            core.quit()
        else:
            time.sleep(1)  # change every 3 sec


def test5(bit, diff=1):
    """
    Show static 6 x 2 colored patches:
        - 1st row with 1-bit step in RGB255
        - 2nd row with 0.2-bit step -- should be distinguishable on 10-bit

    :param bit: 8 or 10
    :param diff: difference in RGB255 scale
    :return:
    """

    color = ColorPicker().Crgb
    color = color.astype(int)

    def changegun(c, d):
        new = c.astype(float)
        new[0] = new[0] + d  # R
        new[1] = new[1] - d  # G
        new[2] = new[2] - d  # B
        return new

    newcolor = changegun(color, diff)

    color1 = [color, color, color, newcolor, newcolor, newcolor]  # upper row

    color2 = [changegun(color, 0.), changegun(color, 0.2), changegun(color, 0.4),
              changegun(color, 0.6), changegun(color, 0.8), changegun(color, 1.0)]  # lower row

    # convert to [-1, 1]
    Crgb = ColorPicker().Crgb / (2 ** 8 - 1) * 2 - 1
    rgb1 = [x / (2 ** 8 - 1) * 2 - 1 for x in color1]
    rgb2 = [x / (2 ** 8 - 1) * 2 - 1 for x in color2]

    win = visual.Window(fullscr=True, color=Crgb, colorSpace='rgb', bpc=(bit, bit, bit), depthBits=bit)

    boundary = 0.8
    num = len(color1)

    colorbar1 = visual.ElementArrayStim(win, units='norm', nElements=num, elementMask=None, elementTex=None,
                                        sizes=(boundary * 2 / num, boundary / 2), colorSpace='rgb')
    colorbar2 = visual.ElementArrayStim(win, units='norm', nElements=num, elementMask=None, elementTex=None,
                                        sizes=(boundary * 2 / num, boundary / 2), colorSpace='rgb')

    colorbar1.xys = [(x, boundary / 4) for x in np.linspace(-boundary, boundary, num, endpoint=False) + boundary / num]
    colorbar2.xys = [(x, - boundary / 4) for x in
                     np.linspace(-boundary, boundary, num, endpoint=False) + boundary / num]

    colorbar1.colors = rgb1

    colorbar2.colors = rgb2
    print(colorbar2.colors)

    colorbar1.draw()
    colorbar2.draw()

    for idx, x in enumerate(np.linspace(-boundary, boundary, num, endpoint=False) + boundary / num):
        text1 = visual.TextStim(win, text=str(color1[idx]), pos=(x, 0.7),
                                height=0.028)  # position set in weird way but works
        text2 = visual.TextStim(win, text=str(color2[idx]), pos=(x, -0.7), height=0.028)
        text1.draw()
        text2.draw()

    win.flip()
    if event.waitKeys():
        win.close()
        return


"""
test 6
"""


def test6(bit, diff=1):
    """
    Dynamic version of test5.

    :param bit: 8 or 10
    :param diff: difference in RGB255 scale
    :return:
    """
    from psychopy.hardware import keyboard
    import time
    # mon = monitors.Monitor(name='VIEWPixx LITE', width=38, distance=57)
    #

    color = ColorPicker().Crgb
    color = color.astype(int)

    def changegun(c, d):
        new = c.astype(float)
        new[0] = new[0] + d  # R
        new[1] = new[1] - d  # G
        new[2] = new[2] - d  # B
        return new

    newcolor1 = changegun(color, diff)
    newcolor2 = changegun(color, -diff)

    color1_1 = [color, color, color, newcolor1, newcolor1, newcolor1]  # upper in condition 1
    color1_2 = [color, color, color, newcolor2, newcolor2, newcolor2]  # upper in condition 2

    color2_1 = [changegun(color, 0.), changegun(color, 0.2), changegun(color, 0.4),
                changegun(color, 0.6), changegun(color, 0.8), changegun(color, 1.0)]

    color2_2 = [changegun(color, 0.), changegun(color, -0.2), changegun(color, -0.4),
                changegun(color, -0.6), changegun(color, -0.8), changegun(color, -1.0)]

    # convert to [-1, 1]
    Crgb = ColorPicker().Crgb / (2 ** 8 - 1) * 2 - 1

    rgb1_1 = [x / (2 ** 8 - 1) * 2 - 1 for x in color1_1]  # upper in condition 1
    rgb1_2 = [x / (2 ** 8 - 1) * 2 - 1 for x in color1_2]  # upper in condition 2

    rgb2_1 = [x / (2 ** 8 - 1) * 2 - 1 for x in color2_1]
    rgb2_2 = [x / (2 ** 8 - 1) * 2 - 1 for x in color2_2]

    win = visual.Window(fullscr=True, color=Crgb, colorSpace='rgb', bpc=(bit, bit, bit), depthBits=bit, units='norm')
    kb = keyboard.Keyboard()

    boundary = 0.8
    num = len(color1_1)

    colorbar1 = visual.ElementArrayStim(win, units='norm', nElements=num, elementMask=None, elementTex=None,
                                        sizes=(boundary * 2 / num, boundary / 2), colorSpace='rgb')
    colorbar2 = visual.ElementArrayStim(win, units='norm', nElements=num, elementMask=None, elementTex=None,
                                        sizes=(boundary * 2 / num, boundary / 2), colorSpace='rgb')

    colorbar1.xys = [(x, boundary / 4) for x in np.linspace(-boundary, boundary, num, endpoint=False) + boundary / num]
    colorbar2.xys = [(x, - boundary / 4) for x in
                     np.linspace(-boundary, boundary, num, endpoint=False) + boundary / num]

    frameN = 0
    while True:
        if frameN % 2:
            rgb1 = rgb1_1
            rgb2 = rgb2_1
            color1 = color1_1
            color2 = color2_1
        else:
            rgb1 = rgb1_2
            rgb2 = rgb2_2
            color1 = color1_2
            color2 = color2_2

        colorbar1.colors = rgb1
        colorbar2.colors = rgb2

        colorbar1.draw()
        colorbar2.draw()

        for idx, x in enumerate(np.linspace(-boundary, boundary, num, endpoint=False) + boundary / num):
            text1 = visual.TextStim(win, text=str(color1[idx]), pos=(x, 0.7),
                                    height=0.028)  # position set in weird way but works
            text2 = visual.TextStim(win, text=str(color2[idx]), pos=(x, -0.7), height=0.028)
            text1.draw()
            text2.draw()

        win.flip()
        frameN += 1

        kb.clock.reset()
        if kb.getKeys():  # press any key to quit
            core.quit()
        else:
            time.sleep(1)  # change every 1 sec


def test5_pyglet(bit):
    """
    Same test as test5, but using pyglet directly instead of Psychopy
    TODO: adjust the size on VIEWPixx
    """
    import pyglet
    from pyglet.gl import gl

    # colors
    def changegun(c, d):
        new = c.astype(float)
        new[0] = new[0] + d  # R
        new[1] = new[1] - d  # G
        new[2] = new[2] - d  # B
        return new

    Crgb = ColorPicker().Crgb
    color = Crgb.astype(int)

    color1 = [color, color, color,
              changegun(color, 1.), changegun(color, 1.), changegun(color, 1.)]

    color2 = [color, changegun(color, .2), changegun(color, .4),
              changegun(color, .6), changegun(color, .8), changegun(color, 1.)]

    # convert to [0, 1]
    Crgb = Crgb / (2 ** 8 - 1)
    rgb1 = [x / (2 ** 8 - 1) for x in color1]
    rgb2 = [x / (2 ** 8 - 1) for x in color2]

    background = (Crgb[0], Crgb[1], Crgb[2], 1)  # RGB and alpha value

    # set up context and window
    # config = pyglet.gl.Config(red_size=bit, gre""" rewrite the test5 with pyglet"""en_size=bit, blue_size=bit)
    config = pyglet.gl.Config(buffer_size=bit * 4)
    winsize = 1200
    window = pyglet.window.Window(caption='OpenGL', resizable=True, config=config, fullscreen=True)

    @window.event
    def on_draw():
        # clears the background with the background color
        gl.glClearColor(*background)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        # draw in a loop
        boundary = winsize - 200
        gap = (winsize - boundary) / 2
        i_width = boundary / len(rgb1)
        i_height = boundary / 2

        # the first line
        for idx, rgb in enumerate(rgb1):
            gl.glColor3f(*rgb)

            gl.glBegin(gl.GL_QUADS)  # start drawing a rectangle in counter-clockwise (CCW) order

            gl.glVertex2f(gap + idx * i_width, gap + i_height)  # bottom left point
            gl.glVertex2f(gap + (idx + 1) * i_width, gap + i_height)  # bottom right point
            gl.glVertex2f(gap + (idx + 1) * i_width, gap + boundary)  # top right point
            gl.glVertex2f(gap + idx * i_width, gap + boundary)  # top left point

            gl.glEnd()

            label = pyglet.text.Label(str(color1[idx]), font_size=10, x=gap + idx * i_width, y=gap + boundary + 20)
            label.draw()

        # # # the second line
        for idx, rgb in enumerate(rgb2):
            gl.glColor3f(*rgb)

            gl.glBegin(gl.GL_QUADS)  # start drawing a rectangle in counter-clockwise (CCW) order

            gl.glVertex2f(gap + idx * i_width, gap)  # bottom left point
            gl.glVertex2f(gap + (idx + 1) * i_width, gap)  # bottom right point
            gl.glVertex2f(gap + (idx + 1) * i_width, gap + i_height)  # top right point
            gl.glVertex2f(gap + idx * i_width, gap + i_height)  # top left point
            gl.glEnd()

            label = pyglet.text.Label(str(color2[idx]), font_size=10, x=gap + idx * i_width, y=gap - 20)
            label.draw()

    pyglet.app.run()


def test6_pyglet(bit):
    """
    Abandoned!!! Not dynamic yet!!!
    Same test as test6, but using pyglet directly instead of Psychopy
    """
    import pyglet
    from pyglet.gl import gl
    from psychopy.hardware import keyboard
    import time

    kb = keyboard.Keyboard()

    # colors
    def changegun(c, d):
        new = c.astype(float)
        new[0] = new[0] + d  # R
        new[1] = new[1] - d  # G
        new[2] = new[2] - d  # B
        return new

    Crgb = ColorPicker().Crgb
    color = Crgb.astype(int)

    newcolor1 = changegun(color, 1)
    newcolor2 = changegun(color, -1)

    color1_1 = [color, color, color, newcolor1, newcolor1, newcolor1]  # upper in condition 1
    color1_2 = [color, color, color, newcolor2, newcolor2, newcolor2]  # upper in condition 2

    color2_1 = [changegun(color, 0.), changegun(color, 0.2), changegun(color, 0.4),
                changegun(color, 0.6), changegun(color, 0.8), changegun(color, 1.0)]

    color2_2 = [changegun(color, 0.), changegun(color, -0.2), changegun(color, -0.4),
                changegun(color, -0.6), changegun(color, -0.8), changegun(color, -1.0)]

    # convert to [0, 1]

    Crgb = Crgb / (2 ** 8 - 1)

    rgb1_1 = [x / (2 ** 8 - 1) for x in color1_1]  # upper in condition 1
    rgb1_2 = [x / (2 ** 8 - 1) for x in color1_2]  # upper in condition 2

    rgb2_1 = [x / (2 ** 8 - 1) for x in color2_1]
    rgb2_2 = [x / (2 ** 8 - 1) for x in color2_2]

    background = (Crgb[0], Crgb[1], Crgb[2], 1)  # RGB and alpha value

    # set up context and window
    # platform = pyglet.window.get_platform()
    # display = platform.get_default_display()
    # screen = display.get_default_screen()

    # template = pyglet.gl.Config(red_size=bit, green_size=bit, blue_size=bit)
    # config = screen.get_best_config(template)
    # context = config.create_context(None)

    # config = pyglet.gl.Config(red_size=bit, green_size=bit, blue_size=bit)
    config = pyglet.gl.Config(buffer_size=bit * 3)

    winsize = 1900
    window = pyglet.window.Window(caption='OpenGL', resizable=True,
                                  config=config, fullscreen=True)

    frameN = 0
    while True:
        if frameN % 2:
            rgb1 = rgb1_1
            rgb2 = rgb2_1
            color1 = color1_1
            color2 = color2_1
        else:
            rgb1 = rgb1_2
            rgb2 = rgb2_2
            color1 = color1_2
            color2 = color2_2

        @window.event
        def on_draw():
            # clears the background with the background color
            gl.glClearColor(*background)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)

            # draw in a loop
            boundary = winsize - 100
            gap = (winsize - boundary) / 2
            i_width = boundary / len(rgb1)
            i_height = boundary / 2

            # the first line
            for idx, rgb in enumerate(rgb1):
                gl.glColor3f(*rgb)

                gl.glBegin(gl.GL_QUADS)  # start drawing a rectangle in counter-clockwise (CCW) order

                gl.glVertex2f(gap + idx * i_width, gap + i_height)  # bottom left point
                gl.glVertex2f(gap + (idx + 1) * i_width, gap + i_height)  # bottom right point
                gl.glVertex2f(gap + (idx + 1) * i_width, gap + boundary)  # top right point
                gl.glVertex2f(gap + idx * i_width, gap + boundary)  # top left point

                gl.glEnd()

                label = pyglet.text.Label(str(color1[idx]), font_size=7, x=gap + idx * i_width, y=gap + boundary + 20)
                label.draw()

            # # # the second line
            for idx, rgb in enumerate(rgb2):
                gl.glColor3f(*rgb)

                gl.glBegin(gl.GL_QUADS)  # start drawing a rectangle in counter-clockwise (CCW) order

                gl.glVertex2f(gap + idx * i_width, gap)  # bottom left point
                gl.glVertex2f(gap + (idx + 1) * i_width, gap)  # bottom right point
                gl.glVertex2f(gap + (idx + 1) * i_width, gap + i_height)  # top right point
                gl.glVertex2f(gap + idx * i_width, gap + i_height)  # top left point
                gl.glEnd()

                label = pyglet.text.Label(str(color2[idx]), font_size=7, x=gap + idx * i_width, y=gap - 20)
                label.draw()

        frameN += 1
        pyglet.app.run()

        kb.clock.reset()
        if kb.getKeys():  # press any key to quit
            core.quit()
        else:
            time.sleep(1)  # change every 1 sec


"""graphics test"""


def graphics_test():
    from pyglet.gl import gl_info
    win = visual.Window([100, 100])  # some drivers want a window open first
    print("\nOpenGL info:")
    # get info about the graphics card and drivers
    print("vendor:", gl_info.get_vendor())
    print("rendering engine:", gl_info.get_renderer())
    print("OpenGL version:", gl_info.get_version())


"""
try them
"""
# test1(10)
# test2()
# test3()
# test4()

# test5(8, 1)
# test6(8)
# test5_pyglet(8)
# graphics_test()
