#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 29 15:03:35 2025
    Combined vacuum vessel
@author: rianc
"""

from VV_Cad import build_VV
from Limiter_test import unsplit_limiter
from arm_extentions_Cad import build_extention_arms
from cyllinder_CAD import build_shield
from cubit_header import thinCurr_path, save_path, cu, check_output, STDOUT

###############################################################################
def do_CAD(doMesh=False,doMesh_all=True,doPlot_eqdsk=False):
    cu.cmd('reset')
    
    grp_id_1,s_lims_1,s_tiles_1 = unsplit_limiter(doMesh=doMesh,in_to_m=True,doReset=True,
                               theta=0.62833062,buildSplit=True,
                               save_ext='_1',skip=[8,12,13],limiter_side_surfs=[21, 22, 23, 24])#[241, 365]
    cu.cmd('Split Body 1 to 6')
    s_end_lim_1 = cu.get_entities('surface')[-1] # Necessary to track for meshing
    
    grp_id_2,s_lims_2,s_tiles_2 = unsplit_limiter(doMesh=doMesh,in_to_m=True,adj_face_id=False,
                               doReset=False,save_ext='_2', limiter_side_surfs=[94,95,96,97,101,105])#[241, 365]
    
    s_lims_1.extend(s_lims_2)
    s_tiles_1=s_tiles_1.tolist()
    s_tiles_1.extend(s_tiles_2)

    s_end_lim_2 = cu.get_entities('surface')[-1] # 
    
    if doMesh: 
        cu.cmd("export genesis 'C_Mod_ThinCurr_Limiters_Combined.g' block 1 to 4 overwrite")
        process_Thincurr('Limiters_Combined')
    

    grp_id_vv=build_VV(s_id_wall=170,doReset=False,doMesh=doMesh,doPlot=doPlot_eqdsk) #328 14 # 104 # 204
    s_end_vv = cu.get_entities('surface')[-1]

    
    s_id_arms, s_id_arm_tiles = build_extention_arms(doReset=False,doMesh=doMesh,)
    
    # Build shielding cyls around Mirnovs
    surf_ids_shield = build_shield(doReset=False,doMesh=doMesh)

    if doMesh_all: 
         build_combined_mesh(s_end_lim_1, s_end_lim_2, s_end_vv,s_lims_1,\
                             s_tiles_1,grp_id_vv, s_id_arms, s_id_arm_tiles,
                             surf_ids_shield)
    elif doMesh:  # Process Limiters and VV separately    
        process_Thincurr('Limiters_Combined')
        process_Thincurr('VV')
    
###############################################################################
def build_combined_mesh(s_end_lim_1, s_end_lim_2, s_end_vv,s_lims,s_lim_tiles,grp_id_vv,
                         s_id_arms, s_id_arm_tiles,surf_ids_shield):
        cu.cmd('delete vertex all')
        cu.cmd('delete curve all')
        
        cu.cmd('imprint all')
        cu.cmd('merge all')
        
        cu.cmd("set trimesher coarse off")
        cu.cmd("set trimesher geometry sizing off")
        cu.cmd("surface all scheme trimesh")
        
        # Limiter 1, 2
        cu.cmd('Surface 1 to %d Size 0.02'%s_end_lim_2) # Modifying this works somehow
        # Adjusting the mesh size for the limiter sides
        s_ = ''
        for i in s_lims: s_+= '%d '%i
        cu.cmd(f'surface {s_} sizing function type skeleton scale 2'+\
                 ' time_accuracy_level 3 min_size .5')
        s_ = ''
        for i in s_lim_tiles: s_+= '%d '%i
        cu.cmd(f'surface {s_} sizing function type skeleton scale 3'+\
                 ' time_accuracy_level 3 min_size 2')
        # Mesh the two limiters
        cu.cmd("mesh surface %d to %d"%(1,s_end_lim_1))
        cu.cmd("mesh surface %d to %d"%(s_end_lim_1+1,s_end_lim_2))

        
        # VV
        cu.cmd('Surface %d to %d Size 0.1'%(s_end_lim_2+1,s_end_vv))
        cu.cmd("mesh group %d"%grp_id_vv) # VV is group 6

        # Arms
        s_ = ''
        for i in s_id_arms: s_+= '%d '%i
        cu.cmd(f'Surface {s_} Size 0.01')
        cu.cmd(f'Block {len(cu.get_entities("block"))+1} surface {s_}')
        s_ = ''
        for i in s_id_arm_tiles: s_+= '%d '%i
        cu.cmd(f'Surface {s_} Size 0.005')
        cu.cmd(f'Block {len(cu.get_entities("block"))+1} Surface {s_}')

        cu.cmd(f"Mesh Surface {'%d'%s_id_arms[0]} to {'%d'%s_id_arm_tiles[-1]}")

        # Shielding Cyllinders
        cu.cmd('Surface %d to %d Size 0.002'%(surf_ids_shield[0],surf_ids_shield[-1]))
        cu.cmd('Mesh Surface %d to %d'%(surf_ids_shield[0],surf_ids_shield[-1]) )

        # Export mesh
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
if __name__ == '__main__': 
     
    do_CAD(doMesh=False, doMesh_all=True)
    # build_VV()
    # process_Thincurr('VV')
