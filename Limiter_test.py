#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 17 13:32:56 2025
    Wrapper for building unsplit limiter
    run in cyllindrical coordinates
    
@author: rianc
"""

#reset 
#!python

import sys;sys.path.append('/home/rianc/Documents/Coreform-Cubit-2025.1/bin/')
import cubit3 as cu
import numpy as np
from copy import copy
from VV_Cad import __load_boundary_gEqdsk

cu.cmd('#reset')
cu.cmd('#undo off')

# constants

# Assume R,Theta,Z coordinates

y_shft = 0 # shift y coorinate to allow side-by-side comparison with CAD


def unsplit_limiter(in_to_m=True,eqdsk_file='g1051202011.1000',doMesh=False):
    cu.cmd('#reset')
    cu.cmd('undo off')
    
    # Coordinates reference the middle of the limiter
    Z_lim = 10.41 # maximum height +/- of the tile edges
    Z_tile_lip = 1.21 # the first and last tile are flat
    R_tile = 32.54
    wall_offset = 0.01 # Offset of limiter from wall [cm]
    R_wall = __get_R_Wall(eqdsk_file,wall_offset)
    R_curve_minima = 36.42 # Radius of deepest curve of limiter
    theta = -3.0105 # origin to center of limiter angle
    
    # Shifts in x, y necessary because edges of limiter are parallel, not rays from origin
    x = lambda r,theta: r*np.cos(theta)
    y = lambda r,theta: r*np.sin(theta) + y_shft
    x1=0.3785
    y1=2.91484
    x_l = lambda r,theta: x(r,theta)-x1; y_l = lambda r,theta: y(r,theta)+y1
    x_r = lambda r,theta: x(r,theta)+x1; y_r = lambda r,theta: y(r,theta)-y1
    
    
    # Build limiter supporting surfaces
    v_up_tile_l, v_down_tile_l, v_up_sub_tile_l, v_down_sub_tile_l, s_lim_surf_l, \
        l_flat_up_l, l_flat_down_l, l_arc_l, v_up_wall_l, v_down_wall_l, l_wall_l = \
        __gen_unsplit_limiter_side(theta,R_wall,R_tile,R_curve_minima,Z_lim,Z_tile_lip,x_l,y_l)
    
    v_up_tile_r, v_down_tile_r, v_up_sub_tile_r, v_down_sub_tile_r, s_lim_surf_r,\
    l_flat_up_r, l_flat_down_r, l_arc_r, v_up_wall_r, v_down_wall_r, l_wall_r = \
        __gen_unsplit_limiter_side(theta,R_wall,R_tile,R_curve_minima,Z_lim,Z_tile_lip,x_r,y_r)

    # Build limiter tile face
    s_face, s_tile_up, s_tile_down =\
        __gen_limiter_face(v_up_tile_l,v_up_tile_r,v_down_tile_l,v_down_tile_r,\
           v_up_sub_tile_l, v_down_sub_tile_l, v_up_sub_tile_r, v_down_sub_tile_r,
                       l_flat_up_l,l_flat_down_l,
                           l_flat_up_r, l_flat_down_r, l_arc_l, l_arc_r)
    
    # Build limiter back
    s_back = __gen_limiter_back(v_up_wall_l, v_down_wall_l, v_up_wall_r, \
                v_down_wall_r, R_wall, theta,Z_lim ,x,y,l_wall_l,l_wall_r)

    #return
    # Cut out holes in side plates
    surf_id_l = __make_cutouts(s_lim_surf_l,-x1,y1,x_l,y_l,theta)
    #
    surf_id_r = __make_cutouts(s_lim_surf_r,x1,-y1,x_r,y_r,theta,extraHoles=True)
    
    # Cut arc curve
    surf_id_r = __make_arc_cutout(surf_id_r,R_tile,theta,Z_lim,Z_tile_lip,x_r,y_r,R_curve_minima)
    
    
    id_group = cu.create_new_group()
    cu.add_entities_to_group(id_group, \
     [surf_id_l, surf_id_r,s_face.id(), s_tile_up.id(),s_tile_down.id(),s_back.id()],\
         'surface')
    cu.cmd('Delete Vertex All')
    if in_to_m: cu.cmd('Group %d Scale %f'%(id_group,0.0254)) # convert to meters if necessary
    
    if doMesh: __do_Mesh()

###################################################
def __gen_unsplit_limiter_side(theta,R_wall,R_tile,R_curve_minima,Z_lim,Z_tile_lip,x,y):
    

    # Build vertex points for limiter wall outline
    v_up_wall = cu.create_vertex(x(R_wall,theta), y(R_wall,theta), +Z_lim)
    v_down_wall = cu.create_vertex(x(R_wall,theta), y(R_wall,theta), -Z_lim)
    
    v_up_tile = cu.create_vertex(x(R_tile,theta), y(R_tile,theta), +Z_lim)
    v_down_tile = cu.create_vertex(x(R_tile,theta), y(R_tile,theta), -Z_lim)
    
    # Build vertex points for flat tile section
    v_up_sub_tile = cu.create_vertex(x(R_tile,theta), y(R_tile,theta), +(Z_lim-Z_tile_lip))
    v_down_sub_tile = cu.create_vertex(x(R_tile,theta), y(R_tile,theta), -(Z_lim-Z_tile_lip))
    
    # Build vertex point for curving tile section
    v_curve_tile_minima = cu.create_vertex(x(R_curve_minima,theta),\
                                           y(R_curve_minima,theta), 0)
    
    # Build outline of limiter wall
    l1 = cu.create_curve(v_up_wall,v_up_tile)
    l_flat_up = cu.create_curve(v_up_tile,v_up_sub_tile)
    
    l_arc = cu.create_arc_curve(v_up_sub_tile,v_down_sub_tile,v_curve_tile_minima.coordinates())
    l_flat_down = cu.create_curve(v_down_sub_tile,v_down_tile)
    l5 = cu.create_curve(v_down_tile,v_down_wall)
    l_wall = cu.create_curve(v_down_wall,v_up_wall)
    
    
    
    # Fill in limiter wall surfacesurf_id
    print( cu.get_entities('vertex')[-1])
    lim_surf = cu.create_surface((l1, l_flat_up, l_arc, l_flat_down, l5, l_wall))
    print('Limiter id ',lim_surf.id(), ' total surfaces ',  cu.get_entities('vertex')[-1])
    # Rebuild vertexes (they are destroyed by surface creator)
    v_up_tile = cu.create_vertex(x(R_tile,theta), y(R_tile,theta), +Z_lim)
    v_down_tile = cu.create_vertex(x(R_tile,theta), y(R_tile,theta), -Z_lim)
    v_up_sub_tile = cu.create_vertex(x(R_tile,theta), y(R_tile,theta), +(Z_lim-Z_tile_lip))
    v_down_sub_tile = cu.create_vertex(x(R_tile,theta), y(R_tile,theta), -(Z_lim-Z_tile_lip))
    v_up_wall = cu.create_vertex(x(R_wall,theta), y(R_wall,theta), +Z_lim)
    v_down_wall = cu.create_vertex(x(R_wall,theta), y(R_wall,theta), -Z_lim)
    
    l_wall = cu.create_curve(v_down_wall,v_up_wall)
    #v_up_wall = cu.create_vertex(x(R_wall,theta), y(R_wall,theta), +Z_lim)
    #v_down_wall = cu.create_vertex(x(R_wall,theta), y(R_wall,theta), -Z_lim)
    
    # Clean up
    __delete_vertex(v_curve_tile_minima)
    
    return v_up_tile, v_down_tile, v_up_sub_tile, v_down_sub_tile,\
        lim_surf, l_flat_up, l_flat_down, l_arc, v_up_wall, v_down_wall, l_wall

####################################################
def __gen_limiter_face(v_up_l,v_up_r,v_down_l,v_down_r,v_sub_up_l,v_sub_down_l, \
                       v_sub_up_r,v_sub_down_r,l_flat_up_l,l_flat_down_l,
                       l_flat_up_r,l_flat_down_r,l_arc,r_arc):
    
    l_top = cu.create_curve(v_up_l,v_up_r)
    l_bot = cu.create_curve(v_down_r,v_down_l)
    
    l_top_sub = cu.create_curve(v_sub_up_l,v_sub_up_r)
    l_bot_sub = cu.create_curve(v_sub_down_r,v_sub_down_l)
    
    s_face = cu.create_surface((l_top_sub,r_arc,l_bot_sub,\
                                l_arc))
        
    s_tile_up = cu.create_surface((l_flat_up_l,l_top,l_flat_up_r,\
                                l_top_sub))
        
    s_tile_down = cu.create_surface((l_flat_down_l,l_bot,l_flat_down_r,\
                                l_bot_sub))
    
    return s_face, s_tile_up, s_tile_down

##########################################################
def __make_cutouts(surface,dx,dy,x,y,theta,extraHoles=False,debug_large=False,debug_small=True):
    # Large cutout
    x0 = -37.23245
    y0 = -4.90455
    z0 = -6.374
    sph_radius = 1.5
    surf_id = surface.id()
    print(surf_id)
    for i in range(2):
        surf_id = __cut_hole(surf_id, sph_radius,\
             x0 + dx - sph_radius*0, y0 + dy+ y_shft, z0*(-1 if i==1 else 1))
    
    ##########################################################################33
    # # Small holes [vertical]
    x0 = -40.2446055
    y0 = -5.2983
    z0 = -9.162
    dz = 0.848
    sph_radius = 0.203
    for i in range(22):
        if i == 8 or i == 13: continue
        
        surf_id = __cut_hole(surf_id, sph_radius,  x0 + dx - sph_radius, y0+dy+ y_shft, z0+dz*i)
    ##########################################################################
    
    # May not need for both sides
    if extraHoles:
        # Horizontal holes
        x0 = -39.8084 + dx
        y0 = -5.21455 + dy+ y_shft
        z0_1 = -10.17045
        z0_2 = -2.25
        dr = 0.7483
        R0 = 40.14848
        radius = 0.141
        for i in range(2):
            for j in range(8): 
                surf_id = __cut_hole(surf_id, radius,\
                 x(R0-dr*j,theta), y(R0-dr*j,theta), z0_1*(-1 if i==1 else 1))
        
            for j in range(4):
                surf_id =  __cut_hole(surf_id, radius,\
                  x(R0-dr*j,theta), y(R0-dr*j,theta), z0_2*(-1 if i==1 else 1))
            
    return surf_id
##############################################################################
def __make_arc_cutout(surf_id,R_tile,theta,Z_lim,Z_tile_lip,x,y,R_curve_minima):
    # Build second tile arch, set back slightly
    dr = 1.095
    radius = 0.141
    v_up_sub_tile = cu.create_vertex(x(R_tile+dr,theta), y(R_tile+dr,theta), +(Z_lim-Z_tile_lip))
    v_down_sub_tile = cu.create_vertex(x(R_tile+dr,theta), y(R_tile+dr,theta), -(Z_lim-Z_tile_lip))
    
    # Build vertex point for curving tile section
    v_curve_tile_minima = cu.create_vertex(x(R_curve_minima+dr,theta),\
                                           y(R_curve_minima+dr,theta), 0)
    
    l_arc = cu.create_arc_curve(v_up_sub_tile,v_down_sub_tile,v_curve_tile_minima.coordinates())
    # Iterarte along curve
    for i in np.linspace(0,1,16,): 
        cu.cmd("create vertex on curve %d fraction %f"%(l_arc.id(),i))
        v_id =  cu.get_entities('vertex')[-1]
        surf_id = __cut_hole_vertex(surf_id,radius,v_id)
        __delete_vertex(v_id)
    
    # Clean up
    cu.cmd("delete curve %d"%l_arc.id())
    __delete_vertex(v_curve_tile_minima)
    
    return surf_id
###############################################################################
def __gen_limiter_back(v_up_wall_l, v_down_wall_l, v_up_wall_r, v_down_wall_r,\
                       R_wall,theta,Z_lim,x,y,l_wall_l,l_wall_r):
    
    print('linking: ',v_up_wall_l.id(),v_up_wall_r.id(),(x(R_wall,theta), y(R_wall, theta), +Z_lim+5) )
    v_mid_up = cu.create_vertex(x(R_wall+0.1,theta), y(R_wall+0.1, theta), +Z_lim)
    print(v_up_wall_l.id(),v_up_wall_r.id())
    #cu.cmd('Create Curve %d %d %d Circular'%(v_up_wall_l.id(),v_up_wall_r.id(),v_mid_up.id()))
    
    l_arc_up = cu.create_arc_curve(v_up_wall_l,v_up_wall_r, \
           (x(R_wall+0.01,theta), y(R_wall+0.01, theta), +Z_lim) )
    l_arc_down = cu.create_arc_curve(v_down_wall_l,v_down_wall_r, \
           (x(R_wall+0.01,theta), y(R_wall+0.01, theta), -Z_lim) )
           
    return cu.create_surface((l_arc_up,l_wall_l,l_arc_down,l_wall_r))
###############################################################################
def __get_R_Wall(eqdsk_file,wall_offset):
    R, Z = __load_boundary_gEqdsk(eqdsk_file,doPlot=False)
    return (np.max(R) - wall_offset) * 1/0.0254 
##########################################################################
def __cut_hole(surf_id,radius,x0,y0,z0,debug=False):
    cu.cmd("create sphere radius %f"%radius)
    sph_id = cu.get_entities('volume')[-1]
    cu.cmd("volume %d move %2.2f %2.2f %2.2f"%(sph_id, x0 ,y0 , z0))
    cu.cmd("subtract volume %d from surface %d"%(sph_id,surf_id ))
    surf_id = cu.get_entities('surface')[-1]
    return surf_id
def __cut_hole_vertex(surf_id,radius,v_id,debug=False):
    cu.cmd("create sphere radius %f"%radius)
    sph_id = cu.get_entities('volume')[-1]
    cu.cmd("move volume %d location vertex %d"%(sph_id, v_id))
    
    cu.cmd("subtract volume %d from surface %d"%(sph_id,surf_id ))
    surf_id = cu.get_entities('surface')[-1]
    return surf_id

##########################################################
def __delete_vertex(verticies):
    if type(verticies) is not list: verticies = [verticies]
    for v in verticies: 
        if type(v) is not int: v = v.id()
        cu.cmd('Delete vertex %d'%v)

##########################################################
def __do_Mesh():
    string  = 'block 1 surface '
    for i in cu.get_entities('surface'): string+= '%d '%i
    cu.cmd(string)
    
    cu.cmd("surface all scheme trimesh")
    cu.cmd('block 1 sizing function type skeleton scale 10'+\
           ' time_accuracy_level 1 min_size .01')
    cu.cmd("mesh block 1")
    
    
    cu.cmd("set large exodus file on")
    cu.cmd("export genesis 'C_Mod_ThinCurr_Limiters.g' overwrite block all")
    
#unsplit_limiter()