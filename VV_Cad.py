#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 17 13:32:56 2025
    Wrapper for building vacuum vessel CAD from eqdsk limiting surfaces
    run in cyllindrical coordinates
    cut holes for ports
@author: rianc
"""

#reset 
#!python

import sys;sys.path.append('/home/rianc/Documents/Coreform-Cubit-2025.1/bin/')
import cubit3 as cu
import numpy as np
try:from freeqdsk import geqdsk
except:import json
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


# constants
# Assume R,Theta,Z coordinates
x_shft = 0# shift y coorinate to allow side-by-side comparison with CAD
m_to_in=False



# Build Vacuum vessel
def build_VV(eqdsk_file='g1051202011.1000',doMesh=False):
    cu.cmd('#reset')
    cu.cmd('undo off')

    # Load in boundary point coordinates
    rlim, zlim =  __load_boundary_gEqdsk(eqdsk_file)
    
    # Build permimter curve, rotation 360deg
    surf_ids = __build_surface(rlim, zlim)
    
    # Cut port holes
    __do_Cut_Ports(surf_ids)
    
    # Group together
    id_group = cu.create_new_group()
    cu.add_entities_to_group(id_group, surf_ids, 'surface')
    
    # Build Mesh
    if doMesh:__do_Mesh()
    
    if m_to_in: 
        cu.cmd('Group %d Scale %f'%(id_group,1/0.0254)) # convert to inces if necessary
        cu.cmd('Delete Vertex All')
    
    return 
################################################################################
def __build_surface(rbdry,zbdry):
    # Start cross-section on y-axis, x=0
    # Build set of lines, combine at end
    
    verticies = []
    for ind in range(len(rbdry)):
        verticies.append( cu.create_vertex(x_shft,rbdry[ind],zbdry[ind]) )
        
    curves_start = cu.get_entities('curve')[-1] +1
    cu.cmd("Create Curve Polyline Vertex %d to %d %d"%\
           (verticies[0].id(),verticies[-1].id(), verticies[0].id()))
    curves_end = cu.get_entities('curve')[-1]
    cu.cmd('Delete Vertex All')
    
    # Spin curves around originE
    cu.cmd('Sweep Curve %d to %d Zaxis Angle 360'%(curves_start, curves_end))
    surf_ids = np.arange(1,cu.get_entities('surface')[-1]+1,dtype=int).tolist()

    return surf_ids

################################################################################
def __load_boundary_gEqdsk(fname,doPlot=False):
    # Load eqdsk file
    try:
        with open(fname,'r') as f: eqdsk=geqdsk.read(f)
    except:
        with open(fname+'.json','r') as f: eqdsk=json.load(f)
        
    # Get boundary points, removing unmeshable or non-axisymmetric points
    rlim = np.delete(eqdsk['rlim'],101 )
    zlim = np.delete(eqdsk['zlim'],101 ) # # Positing radius and width
       
    rlim = np.delete(rlim,np.arange(27,54) )
    zlim = np.delete(zlim,np.arange(27,54) )
    
    # Reduced order model points
    pts = [0,4,8,11,12,13,14,15,16,17,18,20,24,25,28,29,33,35,36,38,39,41,44,47,\
           52, 56, 59,61,62,63,64,65,66,69,71,73,74,75,76,78]
    
    if doPlot:
        plt.close('Limiting surface')
        fig,ax=plt.subplots(1,1,tight_layout=True,figsize=(4,4),num = 'Limiting surface')
        ax.plot(eqdsk['rlim'],eqdsk['zlim'],'-*',ms=3,lw=1,label='Original')
        ax.plot(rlim,zlim,'-*',ms=3,lw=1,label='Axsymmetric Correction')
        
        ax.plot(rlim[pts],zlim[pts],'g*',ms=5,label='Reduced Mesh')
            
        ax.set_xlabel('R [m]')
        ax.set_ylabel('Z [m]')
        ax.grid()
        ax.legend(fontsize=8)
        fig.savefig('Limiting_Surface.pdf',transparent=True)
        plt.show()
        
    return rlim[pts],zlim[pts]

################################################################################
def __do_Cut_Ports(surf_ids):
    R= (41.8)* 0.0254; 
    radial_deg = 4.6144 # degrees for radius/ half width of port
    thicken_depth = 0.00275
    for i in range(10):
        theta_0 = 36*i
        # Build subtraction surface outline
        curves = __make_port_block(i,R,radial_deg,theta_0)
        
        # Subtract from vv wall
        __subtract(curves,surf_ids,theta_0,thicken_depth)
    surf_ids.append( cu.get_entities('surface')[-1]) 
##########################################################
def __make_port_block(i,R,radial_deg,theta_0):

    x = lambda theta: R*np.cos(theta*np.pi/180) + x_shft
    y = lambda theta: R*np.sin(theta*np.pi/180)
    curves = []
    for j in range(2):
        z0 = 8.375*(1 if j==0 else -1) * 0.0254
        dr= 2*np.pi*R*radial_deg/360*(1 if j==0 else -1)
        
        #normal vector for arc and endpoints
        N = (-x(theta_0)*(1 if j==0 else -1),-y(theta_0)*(1 if j==0 else -1),0) 
        v_left = cu.create_vertex(x(theta_0-radial_deg), y(theta_0-radial_deg),z0)
        v_right = cu.create_vertex(x(theta_0+radial_deg), y(theta_0+radial_deg),z0)
        
        # Build top, bottom arch
        c1 = cu.create_arc_curve(v_left, v_right, (x(theta_0), y(theta_0), z0+dr))
        curves.append(c1)
        
        # Vertical section
        v_down = cu.create_vertex(x(theta_0-radial_deg*(1 if j==0 else -1)),\
                y(theta_0-radial_deg*(1 if j==0 else -1)),-z0)
        if j==0: line = cu.create_curve(v_left, v_down)
        else:  line = cu.create_curve(v_right, v_down)
        curves.append(line)
    return curves
#########################################################
def __subtract(curves,surf_ids,theta_0,thicken_depth):
    # Build sutraction object
    s1 = cu.create_surface(curves)
    cu.cmd('Project Surface %d Onto Volume %d'%(s1.id(),surf_ids[188]) ) #13
    s1_id  = cu.get_entities('volume')[-1]
    cu.cmd('Thicken Volume %d Depth %f'%(s1_id, thicken_depth))
    
    s1_id  = cu.get_entities('volume')[-1]
    cu.cmd('Volume %d Move %f %f 0'%(s1_id, \
          -thicken_depth*np.cos(theta_0*np.pi/180)/2, -thicken_depth*np.sin(theta_0*np.pi/180)/2) )
    
    cu.cmd('Subtract Volume %d from volume %d'%(s1_id,surf_ids[188]))
    print(s1_id,surf_ids[188])
    raise SyntaxError
##########################################################
def __do_Mesh():
    
    cu.cmd('imprint all')
    cu.cmd('merge all')
    
    
    cu.cmd("set duplicate block elements off")
    string  = 'block 2 surface '
    for i in cu.get_entities('surface'): string+= '%d '%i
    cu.cmd(string)
    
    cu.cmd("set trimesher coarse off")
    cu.cmd("set trimesher geometry sizing off")

    cu.cmd("surface all scheme trimesh")
    # cu.cmd('surface all sizing function type skeleton scale 10'+\
    #       ' time_accuracy_level 1 min_size .01')
    cu.cmd('Surface All Size 0.1')
    cu.cmd("mesh block 2")
    
    
    cu.cmd("set large exodus file on")
    cu.cmd("export genesis 'C_Mod_ThinCurr_VV.g' overwrite block all")
##########################
#if __name__ == '__main__':build_VV()
    