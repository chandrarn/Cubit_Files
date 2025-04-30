#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 29 15:03:35 2025
    Combined vacuum vessel
@author: rianc
"""

from VV_Cad import build_VV
from Limiter_test import unsplit_limiter

import sys;sys.path.append('/home/rianc/Documents/Coreform-Cubit-2025.1/bin/')
import cubit3 as cu

def do_CAD():
    cu.cmd('reset')
    unsplit_limiter()
    
    build_VV()
    
