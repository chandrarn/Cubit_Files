#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 22 11:23:48 2025
    Header for building C-Mod Cubit Mesh
@author: rianc
"""


thinCurr_path = '~/Documents/OpenFUSIONToolkit/src/utilities/'
save_path = '~/Documents/Synthetic_Mirnov/signal_generation/input_data/' # for saving output data
cubit_path = '/home/rianc/Documents/Coreform-Cubit-2025.1/bin/'

from subprocess import check_output, STDOUT
import numpy as np
try:from freeqdsk import geqdsk
except:pass
import json

import matplotlib.pyplot as plt
from matplotlib import rc
plt.rcParams['figure.figsize']=(6,6)
plt.rcParams['font.weight']='bold'
plt.rcParams['axes.labelweight']='bold'
plt.rcParams['lines.linewidth']=2
plt.rcParams['lines.markeredgewidth']=2
rc('font',**{'family':'serif','serif':['Palatino']})
rc('font',**{'size':11})
rc('text', usetex=True)

# Cubit must be loaded last, otherwise there's path conflicts with the
# package versions stored as part of Cubit's onboard python instance
import sys;sys.path.append(cubit_path)
import cubit3 as cu 
cu.cmd('reset')
cu.cmd('#undo off')