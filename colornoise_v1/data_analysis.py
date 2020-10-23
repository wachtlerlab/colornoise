# !/usr/bin/env python3.7
# -*- coding: utf-8 -*-
""" 
Created on 02.09.20

@author yannansu
"""
from exploredata import session_profile, ExploreData
import os

sub = 'ysu'
res = 'data_analysis_LL/staircase_plots/' + sub
if not os.path.exists(res):
    os.makedirs(res)
xrl = 'data/' + sub + '/' + sub + '.xrl'
with open(xrl) as f:
    lines = f.read().splitlines()
    finished = [line for line in lines if line.endswith('.xlsx')]
xlsx = [f.split(', ')[3] for f in finished]

for x in xlsx:
    index = x.rpartition('/')[-1].rpartition('.xlsx')[0]
    session_profile(xls_file=x, title=x, res_file=res + '/' + sub + '-' + index, show_fig=False)
