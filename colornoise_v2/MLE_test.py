# !/usr/bin/env python3.7
# -*- coding: utf-8 -*-
""" 
Created on 13.10.20

@author yannan
"""
from scipy import stats, special
import numpy as np
from scipy.optimize import minimize
import pylab as py

yy = np.array([0.1,0.15,0.2,0.3,0.7,0.8,0.9, 0.9, 0.95])
xx = np.array(range(0,len(yy),1))

def cumnorm(mu, sd, chance, lapse):
    cum = (special.erf((xx - mu)/(np.sqrt(2) * sd))+1)*0.5
    yPred = chance + (1-lapse-chance) * cum
    # Calculate negative log likelihood
    LL = -np.sum(stats.norm.logpdf(yy, loc=yPred, scale=sd))

    return LL


results = minimize(cumnorm, [], imethod='Nelder-Mead')
print(results.x)

estParms = results.x
yOut = yPred = 1 / (1+ np.exp(-estParms[0]*(xx-estParms[1])))

py.clf()
py.plot(xx,yy, 'go')
py.plot(xx, yOut)
py.show()