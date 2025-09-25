#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    Build extention arms for _TOP/ _BOT mirnov coils

    Hardcoding in sensor locations

"""

from cubit_header import cu, np, json
from Limiter_test import __get_R_Wall

def build_extention_arms(doReset=False,doMesh=False,eqdsk_file='g1051202011.1000'):
    if doReset: cu.cmd('reset')

    # Loop over the necessary number of arms. Save eventually in two 
    # groups, tiles + the arms themselves

    wall_offset = 0.01 # Offset of limiter from wall [m]
    R_wall = __get_R_Wall(eqdsk_file,wall_offset) * 0.0254 

    # Get necessary theta, Z values
    phi, Z, theta = __load_arm_coords()

    s_id_tiles, s_id_arms, group_ids = [], [], []
    for ind,phi in enumerate(phi): 
        build_arm(phi, Z[ind], theta[ind], R_wall, s_id_tiles, s_id_arms,group_ids)

    if doMesh: __doMesh(s_id_arms, s_id_tiles)

    str_ =''
    for i in group_ids: str_+= '%d '%i
    cu.cmd(f'Delete group {str_}')

    cu.create_new_group()
    grp_id = cu.get_entities('group')[-1]

    str_tiles = ''
    for i in s_id_tiles: str_tiles+= '%d '%i
    str_arms = ''
    for i in s_id_arms: str_arms+= '%d '%i

    cu.cmd(f'Group {grp_id} add volume {str_arms} surface {str_tiles}')



    return s_id_arms, s_id_tiles

####################################################################
def build_arm(phi, Z, theta, R_wall, s_id_tiles, s_id_arms,group_ids):
    """
        Build a single arm at angle theta (degrees)
    """

    L_arm = (5.82-.7) * .0254 
    H_W_arm = 0.65 * .0254
     

    # Build arm first
    cu.cmd(f'Create Brick X {L_arm} Y {H_W_arm} Z {H_W_arm}')
    ids_vol = cu.get_entities('volume')[-1]
    s_id_arms.extend( np.arange(cu.get_entities('surface')[-6],cu.get_entities('surface')[-1]+1) )

    for dy in [-0.257, 0.257]:
        for dz in [-0.257, 0.257]:
            # Create shielding tile and move in y-z plane position with respect to arm block
            cu.cmd(f'Create Surface Rectangle width {.45*0.0254} height {.45*0.0254} xplane')        
            s_id_tiles.append( cu.get_entities('surface')[-1] )
            cu.cmd(f'surface {s_id_tiles[-1]} move {0} {dy * .0254 } {dz * .0254 }')
    
    # Adjust shielding tiles to be conformal to plasma
    cu.cmd(f'Rotate Surface {s_id_tiles[-4]} to {s_id_tiles[-1]} about Y angle {90+theta}')
    cu.cmd(f'Surface {s_id_tiles[-4]} to {s_id_tiles[-1]} Move {(5.82 + .255 )/2 * .0254 } 0 0')


    cu.create_new_group()

    group_ids.append( cu.get_entities('group')[-1] )
    id_group = group_ids[-1]
    
    cu.cmd(f'Group {id_group} add volume {ids_vol} surface {s_id_tiles[-4]} to {s_id_tiles[-1]}')

    #raise SyntaxError('Check rotation direction')
    cu.cmd(f'rotate group {id_group} about Z angle {phi+180}')

    cu.cmd(f'group {id_group} move {(R_wall-L_arm/2)*np.cos(phi*np.pi/180)} {(R_wall-L_arm/2)*np.sin(phi*np.pi/180)} {Z}')



####################################################################
def __load_arm_coords():
    # Do HF Mirnovs
    with open('../Synthetic_Mirnov/C-Mod/C_Mod_Mirnov_Geometry_R.json','r',\
                encoding='utf-8') as f: R=json.load(f)
    with open('../Synthetic_Mirnov/C-Mod/C_Mod_Mirnov_Geometry_Z.json','r',\
                encoding='utf-8') as f:  Z=json.load(f)
    with open('../Synthetic_Mirnov/C-Mod/C_Mod_Mirnov_Geometry_Phi.json','r',\
                encoding='utf-8') as f:  phi=json.load(f)     
    with open('../Synthetic_Mirnov/C-Mod/C_Mod_Mirnov_Geometry_Theta_Pol.json','r',\
            encoding='utf-8') as f:  theta_pol=json.load(f)       
    
    Z_out, phi_out, theta_out = [], [], []
    for node_name in R:
        if 'T' in node_name and 'O' in node_name:
            # Boom Extention [Top/Bot] Mirnovs
            phi_out.append( phi[node_name] )
            Z_out.append( Z[node_name] )
            theta_out.append( theta_pol[node_name] )
    
    return phi_out, Z_out, theta_out

####################################################################
def __doMesh(s_id_arms, s_id_tiles):



    cu.cmd('delete vertex all')
    cu.cmd('delete curve all')

    cu.cmd('imprint all')
    cu.cmd('merge all')

    cu.cmd("set trimesher coarse off")
    cu.cmd("set trimesher geometry sizing off")
    cu.cmd("surface all scheme trimesh")

    bl = len(cu.get_entities('block'))+1

    str_arms = ''
    for i in s_id_arms: str_arms+= '%d '%i
    cu.cmd(f'Surface {str_arms} Size 0.01' )
    cu.cmd(f'block {bl} surface {str_arms}')

    str_tiles = ''
    for i in s_id_tiles: str_tiles+= '%d '%i
    cu.cmd(f'Surface {str_tiles} Size 0.005' )
    cu.cmd(f'block {bl+1} surface {str_tiles}')
    
    cu.cmd("mesh surface all")

    cu.cmd(f"export genesis 'C_Mod_ThinCurr_Arms.g' block {bl} to {bl+1} overwrite")

######################################################3
if __name__ == "__main__": build_extention_arms(doReset=True,doMesh=True)