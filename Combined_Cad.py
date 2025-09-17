#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 29 15:03:35 2025
    Combined vacuum vessel
@author: rianc
"""

from VV_Cad import build_VV
from Limiter_test import unsplit_limiter
from cubit_header import thinCurr_path, save_path, cu, check_output, STDOUT

###############################################################################
def do_CAD(doMesh=True,doMesh_all=True,doPlot_eqdsk=False):
    cu.cmd('reset')
    
    grp_id_1 = unsplit_limiter(doMesh=doMesh,in_to_m=True,doReset=True,
                               theta=0.62833062,buildSplit=True,
                               save_ext='_1',skip=[8,12,13])
    cu.cmd('Split Body 1 to 6')
    s_end_lim_1 = cu.get_entities('surface')[-1] # Necessary to track for meshing
    
    grp_id_2 = unsplit_limiter(doMesh=doMesh,in_to_m=True,adj_face_id=True,
                               doReset=False,save_ext='_2', limiter_side_surfs=[241, 365])
    
    s_end_lim_2 = cu.get_entities('surface')[-1] # 
    
    
    cu.cmd("export genesis 'C_Mod_ThinCurr_Limiters_Combined.g' block 1 to 2 overwrite")

    #return
    build_VV(s_id_wall=202,doReset=False,doMesh=doMesh,doPlot=doPlot_eqdsk) #14 # 104
    s_end_vv = cu.get_entities('surface')[-1]
    
    if doMesh_all: build_combined_mesh(s_end_lim_1, s_end_lim_2, s_end_vv)
    else:  # Process Limiters and VV separately
        
        process_Thincurr('Limiters_Combined')
        process_Thincurr('VV')
    
###############################################################################
def build_combined_mesh(s_end_lim_1, s_end_lim_2, s_end_vv):
        cu.cmd('delete vertex all')
        cu.cmd('delete curve all')
        
        cu.cmd('imprint all')
        cu.cmd('merge all')
        
        cu.cmd("set trimesher coarse off")
        cu.cmd("set trimesher geometry sizing off")
        cu.cmd("surface all scheme trimesh")
        
        # Limiter 1, 2
        cu.cmd('Surface 1 to %d Size 0.03'%s_end_lim_2) # Modifying this works somehow
        cu.cmd('surface %d to %d sizing function type skeleton scale 10'%(1,s_end_lim_2)+\
                 ' time_accuracy_level 1 min_size .0075')
        
        cu.cmd("mesh surface %d to %d"%(1,s_end_lim_1))
        cu.cmd("mesh surface %d to %d"%(s_end_lim_1+1,s_end_lim_2))
        
        
        # VV
        cu.cmd('Surface %d to %d Size 0.1'%(s_end_lim_2+1,s_end_vv))
        cu.cmd("mesh group %d"%4)
        
        cu.cmd("set large exodus file on")
        cu.cmd("export genesis 'C_Mod_ThinCurr_Combined.g' block all overwrite")
        
        # Run ThinCurr Conversion
        process_Thincurr('Combined')
###############################################################################
def process_Thincurr(fname):
    print( check_output('python %s'%thinCurr_path+\
        'convert_cubit.py --in_file C_Mod_ThinCurr_%s.g'%fname,\
            shell=True, stderr=STDOUT).decode('utf-8') )
    
    print( check_output('python %s'%thinCurr_path+\
        'scripts/ThinCurr_compute_holes.py --in_file C_Mod_ThinCurr_%s.h5'%fname,\
            shell=True, stderr=STDOUT).decode('utf-8') )
        
    print(check_output('cp C_Mod_ThinCurr_%s-homology.h5'%fname + \
           ' %s'%save_path,  shell=True, stderr=STDOUT).decode('utf-8') )
    print(f'--- Saved C_Mod_ThinCurr_{fname}-homology.h5 to {save_path} ---')
###############################################################################
if __name__ == '__main__': do_CAD()