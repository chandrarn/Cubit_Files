#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 17 13:32:56 2025
    Wrapper for building split, unsplit limiters
    run in cyllindrical coordinates
    
@author: rianc
"""

from VV_Cad import __load_boundary_gEqdsk
from cubit_header import cu, np

# Assume R,Theta,Z coordinates

y_shft = 0 # shift y coorinate to allow side-by-side comparison with CAD


def unsplit_limiter(in_to_m=True,eqdsk_file='g1051202011.1000',
                    doMesh=False,theta=-3.0105,save_ext='',doReset=True,
                    buildSplit=False,adj_face_id=0,skip=[8,13],limiter_side_surfs=[14,10]):#[177,178,179,180]
    if doReset: cu.cmd('reset')
    cu.cmd('undo off')
    v_start = cu.get_entities('volume')[-1]+1 if len(cu.get_entities('volume')) >0 else 1
    s_start= cu.get_entities('surface')[-1]+1 if len(cu.get_entities('surface')) >0 else 1
    
    # Coordinates reference the middle of the limiter
    Z_lim = 10.41 # maximum height +/- of the tile edges
    Z_tile_lip = 1.21 # the first and last tile are flat
    R_tile = 32.54+0.5
    wall_offset = 0.01 # Offset of limiter from wall [cm]
    R_wall = __get_R_Wall(eqdsk_file,wall_offset)
    R_curve_minima = 36.42+0.5 # Radius of deepest curve of limiter
    # theta = -3.0105 origin to center of limiter angle
    # Tile dimensions
    tile_width = 1.46+.0 # in
    tile_height = 1.237+.0  # in
    tile_limiter_offset = 0.66 # in, distance from tile front face to limiter surface
    R_limiter_curve = 0.84/0.0254 # Radius of curvature of limiter, used for tile placement
    
    # Shifts in x, y necessary because edges of limiter are parallel, not rays from origin
    x = lambda r,theta: r*np.cos(theta)
    y = lambda r,theta: r*np.sin(theta) + y_shft
    x1=-2.9175*np.sin(theta)#0.3785
    y1=-2.9175*np.cos(theta)#2.91484
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
    s_face, s_tile_up, s_tile_down = \
        __gen_limiter_face(v_up_tile_l,v_up_tile_r,v_down_tile_l,v_down_tile_r,\
           v_up_sub_tile_l, v_down_sub_tile_l, v_up_sub_tile_r, v_down_sub_tile_r,
                       l_flat_up_l,l_flat_down_l,
                           l_flat_up_r, l_flat_down_r, l_arc_l, l_arc_r)
    
    # Build limiter back
    s_back = __gen_limiter_back(v_up_wall_l, v_down_wall_l, v_up_wall_r, \
                v_down_wall_r, R_wall, theta,Z_lim ,x,y,l_wall_l,l_wall_r)

    
    # Cut out holes in side plates
    surf_id_l = __make_cutouts(s_lim_surf_l,-x1,y1,x_l,y_l,theta,skip=skip,
                               adj_surf_id=adj_face_id,doSplit=buildSplit)

    #
    surf_id_r = __make_cutouts(s_lim_surf_r,x1,-y1,x_r,y_r,theta,skip=skip,
                               extraHoles=True,adj_surf_id=adj_face_id,doSplit=buildSplit)
    
    # Store coordinates along the curved arc for tile placement
    l_arc_points, l_arc_center = __get_arc_points(l_arc_l, frac_points= 15)

    # Cut arc curve
    # surf_id_r = __make_arc_cutout(surf_id_r,R_tile,theta,Z_lim,Z_tile_lip,\
    #                               x_r,y_r,R_curve_minima, buildSplit)
    
    # Split limiter in half if necessary
    if buildSplit:gen_Split(theta,R_wall,s_lim_surf_l,s_lim_surf_r,s_face,s_back,in_to_m)
    #raise SyntaxError
    # Build block for limiter (tiles are done separately)
    v_end = cu.get_entities('volume')[-1]
    s_end = cu.get_entities('surface')[-1]
    id_group = cu.create_new_group()
    cu.cmd('Group %d Add Volume %d to %d'%(id_group,v_start,v_end))
    bl = len(cu.get_entities('block'))+1
    string  = 'block %d surface '%bl
    for i in np.arange(s_start, s_end+1): string+= '%d '%i
    cu.cmd(string)

    
    ##########################################
    # Building tiles to sit just in front of the limiter surface
    block_tiles, start_surf_id_tiles =  __build_tiles(R_curve_minima,s_face, s_tile_up, s_tile_down, tile_width, tile_height,\
                  tile_limiter_offset,l_flat_down_l,l_flat_down_r,l_flat_up_l,l_flat_up_r,buildSplit,
                    in_to_m, x_r,y_r, x_l,y_l, theta,l_arc_points, l_arc_center,R_limiter_curve)
    # Adding the tiles to the limiter sides allows only increasing mesh density for necessary surfaces

    surf_id_tiles = np.arange(start_surf_id_tiles+1, cu.get_entities('surface')[-1]+1)

    # Clean up vertexes and curves
    cu.cmd('Delete Vertex All')
    cu.cmd('Delete Curve All')

    # Scale if desired
    if in_to_m: 
        cu.cmd('Group %d Scale %f'%(id_group,0.0254)) # convert to meters if necessary
        cu.cmd('Group %d Scale %f'%(id_group+1,0.0254)) # convert to meters if necessary

    if doMesh:
        # Meshing handles tiles ok as well
        __do_Mesh(id_group,save_ext,s_lim_surf_l,s_lim_surf_r,s_start, \
                  cu.get_entities('surface')[-1],limiter_side_surfs,bl,surf_id_tiles,buildSplit)

    return id_group, limiter_side_surfs, surf_id_tiles

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
    lim_surf = cu.create_surface((l1, l_flat_up, l_arc, l_flat_down, l5, l_wall))
    
    # Rebuild vertexes (they are destroyed by surface creator)
    v_up_tile = cu.create_vertex(x(R_tile,theta), y(R_tile,theta), +Z_lim)
    v_down_tile = cu.create_vertex(x(R_tile,theta), y(R_tile,theta), -Z_lim)
    v_up_sub_tile = cu.create_vertex(x(R_tile,theta), y(R_tile,theta), +(Z_lim-Z_tile_lip))
    v_down_sub_tile = cu.create_vertex(x(R_tile,theta), y(R_tile,theta), -(Z_lim-Z_tile_lip))
    v_up_wall = cu.create_vertex(x(R_wall,theta), y(R_wall,theta), +Z_lim)
    v_down_wall = cu.create_vertex(x(R_wall,theta), y(R_wall,theta), -Z_lim)
    
    l_wall = cu.create_curve(v_down_wall,v_up_wall)
    
    # Clean up
    __delete_vertex(v_curve_tile_minima)
    
    return v_up_tile, v_down_tile, v_up_sub_tile, v_down_sub_tile,\
        lim_surf, l_flat_up, l_flat_down, l_arc, v_up_wall, v_down_wall, l_wall

###################################################all#
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
def __make_cutouts(surface,dx,dy,x,y,theta,adj_surf_id=0,skip=[8,13],
                   extraHoles=False,debug_large=False,debug_small=True,doSplit=False):
    # Large cutout
    x0 = 38.5541*np.cos(theta)
    y0 = 38.5541*np.sin(theta)
    z0 = -6.374
    sph_radius = 1.5
    surf_id = surface.id()+adj_surf_id
    
    for i in range(2):
        surf_id = __cut_hole(surf_id, sph_radius,\
             x0 + dx - sph_radius*0, y0 + dy+ y_shft, z0*(-1 if i==1 else 1))
    
    return surf_id

    ##########################################################################33
    # # Small holes [vertical]
    x0 = (40.59187+(0.5 if doSplit else -0.3))*np.cos(theta)
    y0 = (40.59187+(0.5 if doSplit else -0.3))*np.sin(theta)
    z0 = -9.162
    dz = 0.848
    sph_radius = 0.203*1.75
    for i in range(22):
        if i in skip: continue
        
        surf_id = __cut_hole(surf_id, sph_radius,  x0 + dx - sph_radius, y0+dy+ y_shft, z0+dz*i)
    ##########################################################################
    
    

    # May not need for both sides
    if extraHoles:
        # Horizontal holes
        x0 = (40.148477)*np.cos(theta) + dx
        y0 = 40.148477*np.sin(theta) + dy + y_shft 
        z0_1 = -9.5#-10.17045
        z0_2 = -2.25 -1
        dr = 0.7483
        R0 = (40.14848 -0.5)
        radius = 0.141*2
        for i in range(2):
            for j in range(8): 
                surf_id = __cut_hole(surf_id, radius,\
                 x(R0-dr*j,theta), y(R0-dr*j,theta), z0_1*(-1 if i==1 else 1))
        
            for j in range(4):
                surf_id =  __cut_hole(surf_id, radius,\
                  x(R0-dr*j,theta), y(R0-dr*j,theta), z0_2*(-1 if i==1 else 1))
            
    return surf_id
##############################################################################
def __make_arc_cutout(surf_id,R_tile,theta,Z_lim,Z_tile_lip,x,y,R_curve_minima,buildSplit=False):
    # Build second tile arch, set back slightly
    dr = (1.095-0.25)
    radius = (0.141*2)
    v_up_sub_tile = cu.create_vertex(x(R_tile+dr,theta), y(R_tile+dr,theta), +(Z_lim-Z_tile_lip))
    v_down_sub_tile = cu.create_vertex(x(R_tile+dr,theta), y(R_tile+dr,theta), -(Z_lim-Z_tile_lip))
    
    # Build vertex point for curving tile section
    v_curve_tile_minima = cu.create_vertex(x(R_curve_minima+dr,theta),\
                                           y(R_curve_minima+dr,theta), 0)
    
    l_arc = cu.create_arc_curve(v_up_sub_tile,v_down_sub_tile,v_curve_tile_minima.coordinates())
    # Iterarte along curve
    for ind,i in enumerate(np.linspace(0,1,16,)): 
        if buildSplit and (5<ind<10): continue # Skip middle section if splitting limiter
         # Create vertex on curve
        cu.cmd("create vertex on curve %d fraction %f"%(l_arc.id(),i))
        v_id =  cu.get_entities('vertex')[-1]
        surf_id = __cut_hole_vertex(surf_id,radius,v_id)
        __delete_vertex(v_id)
    
    # Clean up
    cu.cmd("delete curve %d"%l_arc.id())
    # __delete_vertex(v_curve_tile_minima)
    
    return surf_id
###############################################################################
def __gen_limiter_back(v_up_wall_l, v_down_wall_l, v_up_wall_r, v_down_wall_r,\
                       R_wall,theta,Z_lim,x,y,l_wall_l,l_wall_r):
    
    v_mid_up = cu.create_vertex(x(R_wall+0.1,theta), y(R_wall+0.1, theta), +Z_lim)

    l_arc_up = cu.create_arc_curve(v_up_wall_l,v_up_wall_r, \
           (x(R_wall+0.01,theta), y(R_wall+0.01, theta), +Z_lim) )
    l_arc_down = cu.create_arc_curve(v_down_wall_l,v_down_wall_r, \
           (x(R_wall+0.01,theta), y(R_wall+0.01, theta), -Z_lim) )
           
    return cu.create_surface((l_arc_up,l_wall_l,l_arc_down,l_wall_r))

###############################################################################
def __get_arc_points(l_arc, frac_points=15):
    center_point = l_arc.curve_center()
    l_points = []
    for i in np.linspace(1/frac_points/2,1-1/frac_points/2,frac_points,endpoint=True): 
        l_points.append( l_arc.position_from_fraction(i) )
    
    return l_points, center_point
###############################################################################
def __build_tiles(R_curve_minima,s_face, s_tile_up, s_tile_down, tile_width, tile_height,\
                  tile_limiter_offset,l_flat_down_l,l_flat_down_r,l_flat_up_l,l_flat_up_r,\
                    buildSplit, in_to_m ,x_r,y_r, x_l,y_l, theta, l_arc_points, l_arc_center,
                    R_limiter_curve):
    # There are four columns of tiles
    # get into plane of tile-lip
    # use arc center to define motion along the arc
    # 
    tile_correction_width = 1.04 # Unclear why this is necessary, but without it the tiles don't line up properly
    prev_surf_ids = cu.get_entities('surface')[-1]
    prev_vol_ids = cu.get_entities('volume')[-1]

    for horiz in range(4):
        
        for vert in range(2):
            
            
            # Get vector of positions for upper, lower flat section for tiles
            if vert ==0: # if operating on lower tile
                v_l = l_flat_down_l.vertices()
                v_r = l_flat_down_r.vertices()
            else:
                v_l = l_flat_up_l.vertices()
                v_r = l_flat_up_r.vertices()

            # Ensure that we're operating on the upper two verticies in the flat section
            v_l = v_l[0] if v_l[0].coordinates()[2] > v_l[1].coordinates()[2] else v_l[1]
            v_r = v_r[0] if v_r[0].coordinates()[2] > v_r[1].coordinates()[2] else v_r[1]

            # vector along top of flat section
            vec_flat = np.array(v_r.coordinates()) - np.array(v_l.coordinates())
           
            # Move along flat section
            vec_flat = vec_flat/np.linalg.norm(vec_flat) * (tile_width/2 + tile_correction_width*horiz/4*(np.linalg.norm(vec_flat)))
            # Get angle of tile center
            theta_tile = np.arctan2(v_l.coordinates()[1]+vec_flat[1], v_l.coordinates()[0]+vec_flat[0])

            # Build tile
            cu.cmd('create surface rectangle width %f height %f xplane'%(tile_height,tile_width))
            s_tile_new = cu.get_entities('surface')[-1]            

             # Rotate to face limiter
            cu.cmd('rotate surface %d about Z angle %f'%\
                     (s_tile_new, theta_tile*180/np.pi +4 -2*horiz) ) # 4 degree twist to match tile twist)
             
            # Move into position, Drop to middle of flat section
            cu.cmd('surface %d move %f %f %f'%\
                   (s_tile_new, v_l.coordinates()[0]+vec_flat[0],\
                    v_l.coordinates()[1]+vec_flat[1], v_l.coordinates()[2]+vec_flat[2] -tile_height/2) )
            
           
            # move out slightly from limiter face
            cu.cmd('surface %d move %f %f 0'%\
                     (s_tile_new, -np.cos(theta_tile)*tile_limiter_offset,\
                        -np.sin(theta_tile)*tile_limiter_offset))
            
        ################################################
        # Curved section
        # get vector from bottom of top flat section, one side, to top of bottom flat section, same
        # That angle sets max/min of arc, arc radius is R_curve_minima
        # Use the previous 

         # Get vector of positions for upper, lower flat section for tiles
        
        v_l_d = l_flat_down_l.vertices()
        v_r_d = l_flat_down_r.vertices()
        
        v_l_u = l_flat_up_l.vertices()
        v_r_u = l_flat_up_r.vertices()

        # Ensure that we're operating on the upper verticies in the lower flat section, and vice versa
        v_l_d = v_l_d[0] if v_l_d[0].coordinates()[2] > v_l_d[1].coordinates()[2] else v_l_d[1]
        v_r_d = v_r_d[0] if v_r_d[0].coordinates()[2] > v_r_d[1].coordinates()[2] else v_r_d[1]
        v_l_u = v_l_u[0] if v_l_u[0].coordinates()[2] < v_l_u[1].coordinates()[2] else v_l_u[1]

        # vector along top of flat section
        vec_flat = np.array(v_r_d.coordinates()) - np.array(v_l_d.coordinates())
        
        # Move along flat section
        vec_flat = vec_flat/np.linalg.norm(vec_flat) * (tile_width/2 + tile_correction_width*horiz/4*(np.linalg.norm(vec_flat)))
        # Get angle of tile center
        theta_tile = np.arctan2(v_l_d.coordinates()[1]+vec_flat[1], v_l_d.coordinates()[0]+vec_flat[0])

        l_arc_center = np.array([R_limiter_curve*np.cos(theta),R_limiter_curve*np.sin(theta),0]) 
        theta_arc = -0.790843609840896#np.arctan2(l_arc_points[-1][1]-l_arc_center[1], l_arc_points[-1][0]-l_arc_center[0]) +np.pi/4


        
        # Place tile at correct location along arc
        for ind,angle in enumerate(np.linspace(0, 2*theta_arc, 15,endpoint=True)):
            if buildSplit and 5<ind<9: continue

            # Build tile
            cu.cmd('create surface rectangle width %f height %f xplane'%(tile_height,tile_width))
            s_tile_new = cu.get_entities('surface')[-1]            

            # Rotate to face limiter
            cu.cmd('rotate surface %d about Y angle %f'%\
                        (s_tile_new, (theta_arc-angle)*180/np.pi) ) # rotate to match arc angle
            
            cu.cmd('rotate surface %d about Z angle %f'%\
                        (s_tile_new, theta_tile*180/np.pi +4 -2*horiz) ) # 4 degree twist to match tile twist)
            
            
            x_ =  x_l(R_curve_minima+1*tile_limiter_offset,angle) #+ x_r(R_curve_minima+1*tile_limiter_offset,theta_tile) )/2
            y_ =  y_l(R_curve_minima+1*tile_limiter_offset,angle) #+ y_r(R_curve_minima+1*tile_limiter_offset,theta_tile) )/2
            
            # test increasing x, y as angle gets closer to zero

            x_arc = x_#(R_curve_minima-tile_limiter_offset)*np.cos(theta_tile)
            y_arc = y_#(R_curve_minima-tile_limiter_offset)*np.sin(theta_tile)
            z_arc = (R_curve_minima-0*tile_limiter_offset)*np.sin(angle)
            
            

            # Move along flat section
            cu.cmd('surface %d move %f %f %f'%\
                   (s_tile_new, l_arc_points[ind][0]+vec_flat[0],\
                    l_arc_points[ind][1]+vec_flat[1], l_arc_points[ind][2]+vec_flat[2] ) )
            
           
            # # move out slightly from limiter face
            cu.cmd('surface %d move %f %f %f'%\
                     (s_tile_new, -np.cos(theta_tile)*tile_limiter_offset,\
                        -np.sin(theta_tile)*tile_limiter_offset,np.sin(theta_arc-angle)*tile_limiter_offset))
            
            # # Move to arc location
            # cu.cmd('surface %d move %f %f %f'%\
            #        (s_tile_new, x_arc, y_arc, z_arc) )
            
            
            # # move out slightly from limiter face
            # cu.cmd('surface %d move %f %f 0'%\
            #          (s_tile_new, -np.cos(theta_tile)*tile_limiter_offset,\
            #             -np.sin(theta_tile)*tile_limiter_offset))
        # Build tile
        # cu.cmd('create surface rectangle width %f height %f xplane'%(tile_width,tile_height))
        # s_tile_new = cu.get_entities('surface')[-1]

    v_end = cu.get_entities('volume')[-1]
    id_group = cu.create_new_group()
    
    
    # raise SyntaxError
    cu.cmd('Group %d Add Volume %d to %d'%(id_group,prev_vol_ids+1,v_end))
    # cu.cmd('Delete Vertex All')
    # cu.cmd('Delete Curve All')
    # if in_to_m: cu.cmd('Group %d Scale %f'%(id_group,0.0254)) # convert to meters if necessary
    
    
    bl = len(cu.get_entities('block'))+1
    string  = 'block %d surface '%bl
    for i in np.arange(prev_surf_ids+1, cu.get_entities('surface')[-1]+1): string+= '%d '%i
    cu.cmd(string)

    return bl, prev_surf_ids

###############################################################################
def gen_Split(theta,R_wall,s_lim_surf_l,s_lim_surf_r,s_face,s_back,in_to_m,H_Split=4):
    R_cut = R_wall - 4
    # Cut middle out of split limiter
    cu.cmd("Create Brick X 10 Y 10 Z %f"%(H_Split))
    v_brick = cu.get_entities('volume')[-1]
    cu.cmd('Volume %d Rotate %f About Z'%(v_brick,theta*np.pi/180))
    cu.cmd('Volume %d Move %f %f 0'%(v_brick, R_cut*np.cos(theta), R_cut*np.sin(theta)) )
    
    cu.cmd('Subtract Volume %d from Volume 1 to %d'%(v_brick,v_brick-1))
    
    # Building covering surface unfortunately has to be hardcoded
    bounding_curves_1 = np.array([145, 133, 139, 127]) -79#+ 25
    bounding_curves_2 = np.array([124, 142, 130, 136]) -79#+ 25
    cu.cmd(f'Create Surface Curve {bounding_curves_1[0]} {bounding_curves_1[1]} {bounding_curves_1[2]} {bounding_curves_1[3]}')
    cu.cmd(f'Create Surface Curve {bounding_curves_2[0]} {bounding_curves_2[1]} {bounding_curves_2[2]} {bounding_curves_2[3]}')
    s_new = [cu.get_entities('volume')[-2], cu.get_entities('volume')[-1] ]
   
   
    cu.cmd('Create Cylinder Height 5 Radius 1')
    v_cyl = cu.get_entities('volume')[-1]
    cu.cmd('Volume %d Move %f %f 0'%\
           (v_cyl, (R_wall-2)*np.cos(theta),(R_wall-2)*np.sin(theta)) )
    cu.cmd('Subtract Volume %d from Volume %d %d'%(v_cyl, s_new[0], s_new[1]))

###############################################################################
def __get_R_Wall(eqdsk_file,wall_offset):
    R, Z = __load_boundary_gEqdsk(eqdsk_file,doPlot=False)
    return (np.max(R) - wall_offset) * 1/0.0254 
##########################################################################
def __cut_hole(surf_id,radius,x0,y0,z0,debug=False):
    cu.cmd("create sphere radius %f"%radius)
    sph_id = cu.get_entities('volume')[-1]
    cu.cmd("volume %d move %2.2f %2.2f %2.2f"%(sph_id, x0 ,y0 , z0))
    cu.cmd("subtract volume %d from volume %d"%(sph_id,surf_id ))
    return surf_id

def __cut_hole_vertex(surf_id,radius,v_id,debug=False):
    cu.cmd("create sphere radius %f"%radius)
    sph_id = cu.get_entities('volume')[-1]
    cu.cmd("move volume %d location vertex %d"%(sph_id, v_id))
    
    cu.cmd("subtract volume %d from volume %d"%(sph_id,surf_id ))
    return surf_id

##########################################################
def __delete_vertex(verticies):
    if type(verticies) is not list: verticies = [verticies]
    for v in verticies: 
        if type(v) is not int: v = v.id()
        cu.cmd('Delete vertex %d'%v)

##########################################################
def __do_Mesh(id_group,save_ext,s_lim_surf_l,s_lim_surf_r,s_start,s_end,\
              limiter_side_surfs,first_block,surf_id_tiles,doSplit):
    cu.cmd('delete vertex all')
    
    cu.cmd('imprint body %d to %d'%(s_start,s_end))
    cu.cmd('merge body %d to %d'%(s_start,s_end))
    cu.cmd("set duplicate block elements off")

    cu.cmd("merge surface %d to %d"%(s_start,s_end))
    # Test adaptive mesh only on limiter sides
    #     
    if not doSplit: 

        print(s_start,s_end,limiter_side_surfs,surf_id_tiles)
        #raise SyntaxError
    #raise SyntaxError
    cu.cmd("surface all scheme trimesh")
        
    cu.cmd("set trimesher coarse off")
    cu.cmd("set trimesher geometry sizing off")
    cu.cmd("surface all scheme trimesh")
    cu.cmd('Surface all Size 1') 

    s_ = ''
    for i in surf_id_tiles: s_+= '%d '%i #surf_id_tiles
    #cu.cmd('Surface {s_} Size 0.001') 
    cu.cmd(f'surface {s_} sizing function type skeleton scale 3.'+\
             ' time_accuracy_level 3 min_size 2')

    # Finer mesh on limiter sides
    s_ = ''
    for i in limiter_side_surfs: s_+= '%d '%i #limiter_side_surfs
    cu.cmd(f'surface {s_} sizing function type skeleton scale 2.'+\
             ' time_accuracy_level 3 min_size .5')
    
    cu.cmd("mesh surface %d to %d"%(s_start,s_end))
    #raise SyntaxError
    cu.cmd("set large exodus file on")
    cu.cmd("export genesis 'C_Mod_ThinCurr_Limiters%s.g' block %d %d overwrite"%\
           (save_ext,first_block, first_block+1))


######################################################3
if __name__ == "__main__": 
    # unsplit_limiter(doMesh=False,in_to_m=True,doReset=True,)
    unsplit_limiter(doMesh=True,in_to_m=True,doReset=True,)
    # unsplit_limiter(doMesh=False,in_to_m=True,doReset=True,theta=0.62833062,buildSplit=True,skip=[8,12,13])