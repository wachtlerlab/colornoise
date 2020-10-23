#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python version 3.5.2

"""
This module keeps a record of all parameter files (*.par) that have been generated.
Usually you only need to generate a *.par file once and be careful about overwriting!!!

Pitfalls at the moment: you need to modify parameters in genconfig.py, no input available in this module except for random seeds.

Tip: the *.par file name cannot contain numerical strings!!! Otherwise errors in reading stairs!!!

@author: yannansu
"""

from genconfig import writepar


# # sequential
# writepar(stimulus, 'seq')
#
# # pseudo-random with specific seed
# np.random.seed(10)
# rnd_a = np.random.permutation(stimulus)
# writepar(rnd_a, 'rnd_a')
#
# np.random.seed(20)
# rnd_b = np.random.permutation(stimulus)
# writepar(rnd_b, 'rnd_b')
#
# # c and d use different start values and step sizes
# np.random.seed(30)
# rnd_c_new = np.random.permutation(stimulus)
# writepar(rnd_c_new, 'rnd_c_new')
#
# np.random.seed(40)
# rnd_d = np.random.permutation(stimulus)
# writepar(rnd_d, 'rnd_d')

## new steptype with 'lin'

# np.random.seed(10)
# rnd_a = np.random.permutation(stimulus)
# writepar(rnd_a, 'rnd_a')

# ## back to db steptypes
# np.random.seed(20)
# rnd_b = np.random.permutation(stimulus)
# writepar(rnd_b, 'rnd_b')
# #
# np.random.seed(30)
# rnd_c = np.random.permutation(stimulus)
# writepar(rnd_c, 'rnd_c')

# np.random.seed(30)
# rnd_f = np.random.permutation(stimulus)
# writepar(rnd_f, 'rnd_f')

# np.random.seed(30)
# rndq_a = np.random.permutation(stimulus)
# writepar(rndq_a, 'rndq_a', quest=True)

# np.random.seed(30)
# rnd_g = np.random.permutation(stimulus)
# writepar(rnd_g, 'rnd_g')

# np.random.seed(10)
# rnd_h = np.random.permutation(stimulus)
# writepar(rnd_h, 'rnd_h')

##################################################
## new par in 2020 Feb

# np.random.seed(10)
# rnd_a = np.random.permutation(stimulus)
# writepar(rnd_a, 'rnd_a', 'db', quest=None)

# np.random.seed(20)  # nReversals = 2
# rnd_b = np.random.permutation(stimulus)
# writepar(rnd_b, 'rnd_b', 'db', quest=None)

# np.random.seed(30)  # nReversals = 3
# rnd_c = np.random.permutation(stimulus)
# writepar(rnd_c, 'rnd_c', 'db', quest=None)

##################################################
## test linear steps
# np.random.seed(10)
# rnd_a_lin = np.random.permutation(stimulus)
# writepar(rnd_a_lin, 'rnd_a_lin', 'lin', quest=None)

# np.random.seed(20)
# rnd_b_lin = np.random.permutation(stimulus)
# writepar(rnd_b_lin, 'rnd_b_lin', 'lin', quest=None)

# np.random.seed(20)
# rnd_lin_newtest = np.random.permutation(stimulus)
# writepar(rnd_lin_newtest, 'rnd_lin_newtest', 'lin', quest=None)


# # new linear step with seed 10
# writepar().writeparam(10, 'rnd_lin_newtest', 'lin', quest=None)

# writepar().writeparam(10, 'rnd_lin_newtest_copy', 'lin', quest=None)

###################################################
# # test high-noise

# # H-H codition with seed 10, std 2
# writepar().writeparam(10, 'rnd_high_a', 'lin', quest=None)
#
# # H-H codition with seed 20, std 5
# writepar().writeparam(20, 'rnd_high_b', 'lin', quest=None)
#
# #H-H codition with seed 30, std 7.5
# writepar().writeparam(30, 'rnd_high_c', 'lin', quest=None)
#
# # H-H codition with seed 40, std 10
# writepar().writeparam(40, 'rnd_high_d', 'lin', quest=None)

###################################################
# try to determine a do-able linear method (low-noise)
#
# with nReversals = 3, nUp=1, nDown=2
# writepar().writeparam(5, 'rnd_lin_final_a', 'lin', quest=None)
#
# with nReversals = 2, nUp=1, nDown=2
# writepar().writeparam(15, 'rnd_lin_final_b', 'lin', quest=None)
#
# with nReversals = 2. nUp=2, nDown=1
# writepar().writeparam(20, 'rnd_lin_final_c', 'lin', quest=None)
#
# with nReversals = 2. nUp=2, nDown=2
# writepar().writeparam(25, 'rnd_lin_final_d', 'lin', quest=None)