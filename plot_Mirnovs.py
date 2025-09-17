#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May  9 17:13:43 2025
 Plot sensor locations
 
@author: rianc
"""

import sys
sys.path.append('../Synthetic_Mirnov/C-Mod/')
sys.path.append('/home/rianc/Documents/Coreform-Cubit-2025.1/bin/')
import cubit3 as cu
import json
import numpy as np

def place_Mirnovs(sensor_set='Mirnov',limiter_only=True):
    
    if sensor_set == 'Mirnov':
        cu.cmd('Delete Volume in Mirnov')
        # Do HF Mirnovs
        with open('../Synthetic_Mirnov/C-Mod/C_Mod_Mirnov_Geometry_R.json','r',\
                  encoding='utf-8') as f: R=json.load(f)
        with open('../Synthetic_Mirnov/C-Mod/C_Mod_Mirnov_Geometry_Z.json','r',\
                  encoding='utf-8') as f:  Z=json.load(f)
        with open('../Synthetic_Mirnov/C-Mod/C_Mod_Mirnov_Geometry_Phi.json','r',\
                  encoding='utf-8') as f:  phi=json.load(f)        
        
        # Loop
        
        sph_id = []
        for node_name in R:
            if 'T' in node_name and not 'O' in node_name:
            # Do Tile Mirnovs [Note: R adjustment to move mirnov under mesh, and phi offset shift for aligmnent 
            # with CAD in Mirnov_Geometry within mirnov_Probe_Geometry]
                phase_offset=0
                R_adj = 0# 0.01 Movded to gen_MAGX_Coords
                __place_Mirnov_sensor(node_name, R, Z, phi, phase_offset, R_adj,sph_id)
            elif 'O' in node_name: 
                if limiter_only: continue
                # Boom Extention [Top/Bot] Mirnovs
                phase_offset=0
                R_adj = 0# 0.01 Movded to gen_MAGX_Coords
                __place_Mirnov_sensor(node_name, R, Z, phi, phase_offset, R_adj,sph_id)
            else: # Limiter side Mirnovs
                phase_offset = 0
                R_adj = 0# 0.01 Movded to gen_MAGX_Coords
                __place_Mirnov_sensor(node_name, R, Z, phi, phase_offset, R_adj,sph_id)
        #id_group = cu.create_new_group()
        cu.cmd('Group "Mirnov" Equals Volume %d to %d'%( sph_id[0],sph_id[-1]))
    
    if sensor_set == 'BP':
        cu.cmd('Delete Group "BP"')
        # Do HF Mirnovs
        with open('../Synthetic_Mirnov/C-Mod/C_Mod_BP_Geometry_X.json','r',\
                  encoding='utf-8') as f: X=json.load(f)
        with open('../Synthetic_Mirnov/C-Mod/C_Mod_BP_Geometry_Y.json','r',\
                  encoding='utf-8') as f:  Y=json.load(f)
        with open('../Synthetic_Mirnov/C-Mod/C_Mod_BP_Geometry_Z.json','r',\
                  encoding='utf-8') as f:  Z=json.load(f)   
            
        sph_id = []
        for node_name in X:
            cu.cmd("create sphere radius %f"%.01)
            sph_id.append( cu.get_entities('volume')[-1] )
            cu.cmd("move volume %d X %f Y %f Z %f"%(sph_id[-1],X[node_name],\
                                                    Y[node_name],Z[node_name]) )
        cu.cmd('Group "BP" Equals Volume %d to %d'%( sph_id[0],sph_id[-1]))

# Helper function to place Mirnov sensors
def __place_Mirnov_sensor(node_name, R, Z, phi, phase_offset, R_adj,sph_id):
    cu.cmd("create sphere radius %f"%.01)
    sph_id.append( cu.get_entities('volume')[-1] )
    cu.cmd("move volume %d X %f Y %f Z %f"%(sph_id[-1], \
            (R[node_name] + R_adj)*np.cos(phi[node_name]*np.pi/180 + phase_offset*np.pi/180), 
            (R[node_name] + R_adj)*np.sin(phi[node_name]*np.pi/180 + phase_offset*np.pi/180), 
            Z[node_name]) ) 
    cu.cmd("color volume %d rgb 0 0 0"%sph_id[-1])

if __name__=='__main__':place_Mirnovs()