#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Test for Stainless steel cyllindar

from cubit_header import cu, np, json


def build_shield(doReset=False,doMesh=False):

    if doReset: cu.reset()
    
    #Dimensions
    C_height = 13e-3
    C_diam = 4e-3

    R, Z, phi, theta_pol = __load_probes()

    surf_ids = []
    for ind, node_name in enumerate(R):
        print(f'Building cyl for {node_name} at R={R[node_name]}, Z={Z[node_name]}, phi={phi[node_name]}')
        vol_id_cyl,surf_id_cyl = __build_Cylinder( C_diam, C_height)
        
        cu.cmd(f'Surface {surf_id_cyl} Move 0 0 {-C_height/2}') # Move to center at z=0
        cu.cmd(f'Rotate Surface {surf_id_cyl} about Y Angle {-theta_pol[node_name]+90}')
        cu.cmd(f'Rotate Surface {surf_id_cyl} about Z Angle {phi[node_name]}')
        
        

        cu.cmd(f'Surface {surf_id_cyl} Move {R[node_name]*np.cos(phi[node_name]*np.pi/180)} '+\
               f'{R[node_name]*np.sin(phi[node_name]*np.pi/180)} {Z[node_name]}')
        #return
        surf_ids.append(surf_id_cyl)
    
    grp_id = cu.create_new_group()
    str_ = ''
    for i in surf_ids: str_+= '%d '%i
    cu.cmd(f'Group {grp_id} add surface {str_}')

    cu.cmd(f'Block {len(cu.get_entities("block"))+1} surface {str_}')

    if doMesh:
        cu.cmd('surface all scheme trimesh')
        cu.cmd(f'Surface {str_} Size 0.01')
        
        cu.cmd(f'Mesh Surface {str_}')

    return surf_ids
###############################################################################
def __build_Cylinder( C_diam, C_height):
    # Build initial surface
    last_surf_id = cu.get_entities('surface')[-1] if len(cu.get_entities('surface'))>0 else 0
    cu.cmd('Create Vertex 0 0 0')
    v_id = cu.get_entities('vertex')[-1]
    cu.cmd(f'Create Curve Arc Vertex {v_id} radius {C_diam/2} normal 0 0 1 full')
    c_id = cu.get_entities('curve')[-1]
    cu.cmd(f'Sweep Curve {c_id} vector 0 0 1 Distance {C_height}')
    cu.cmd(f'Delete Vertex {v_id}') 
    vol_id_cyl = cu.get_entities('volume')[-1]
    surf_id_cyl = cu.get_entities('surface')[-1]

    return vol_id_cyl,surf_id_cyl


##################################################################
def __load_probes():
    with open('../Synthetic_Mirnov/C-Mod/C_Mod_Mirnov_Geometry_R.json','r',\
                encoding='utf-8') as f: R=json.load(f)
    with open('../Synthetic_Mirnov/C-Mod/C_Mod_Mirnov_Geometry_Z.json','r',\
                encoding='utf-8') as f:  Z=json.load(f)
    with open('../Synthetic_Mirnov/C-Mod/C_Mod_Mirnov_Geometry_Phi.json','r',\
                encoding='utf-8') as f:  phi=json.load(f)     
    with open('../Synthetic_Mirnov/C-Mod/C_Mod_Mirnov_Geometry_Theta_Pol.json','r',\
            encoding='utf-8') as f:  theta_pol=json.load(f)       
    


    return R, Z, phi, theta_pol

################################################################################
if __name__ == "__main__":
    build_shield(doReset=True,doMesh=True)