#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 17 13:32:56 2025
    Wrapper for building vacuum vessel CAD from eqdsk limiting surfaces
    run in cyllindrical coordinates
    cut holes for ports
@author: rianc
"""

from cubit_header import cu, np, plt, rc
# Cubit GUI can't import nonstandard libraries, although you can run the scripts directly
# from your editor/terminal
try: from cubit_header import geqdsk 
except: from cubit_header import json 

# constants
# Assume R,Theta,Z coordinates
x_shft = 0# shift y coorinate to allow side-by-side comparison with CAD
m_to_in=False


# Build Vacuum vessel
def build_VV(eqdsk_file='g1051202011.1000',doMesh=True,s_id_wall=14,
             doReset=True,save_Ext='',doPlot=False):
    if doReset: cu.cmd('reset')
    cu.cmd('undo off')
    s_0 = cu.get_entities('surface')[-1] if len(cu.get_entities('surface')) >0 else 0
    v_0 = cu.get_entities('volume')[-1] if len(cu.get_entities('volume')) >0 else 1
    c_0 = cu.get_entities('curve')[-1] if len(cu.get_entities('curve')) >0 else 0

    # Load in boundary point coordinates
    rlim, zlim =  __load_boundary_gEqdsk(eqdsk_file,doPlot)
    
    # Build permimter curve, rotation 360deg
    surf_ids = __build_surface(rlim, zlim, c_0,s_0)
    # return

    # Cut port holes
    __do_Cut_Ports(surf_ids,s_id_wall)
    
    # Group together
    id_group = cu.create_new_group()
    cu.add_entities_to_group(id_group, surf_ids, 'surface')
    

    
    if m_to_in: 
        cu.cmd('Group %d Scale %f'%(id_group,1/0.0254)) # convert to inces if necessary
    
    # Do Blocking here
    bl = len(cu.get_entities('block'))+1
    cu.cmd("set duplicate block elements off")
    string  = 'block %d add surface '%bl
    for i in surf_ids: string+= '%d '%i
    cu.cmd(string)
    
    # Build Mesh
    if doMesh:__do_Mesh(s_0, id_group,surf_ids,save_Ext)
        
    return 
################################################################################
def __build_surface(rbdry,zbdry,c_0,s_0):
    # Start cross-section on y-axis, x=0
    # Build set of lines, combine at end
    
    verticies = []
    for ind in range(len(rbdry)):
        verticies.append( cu.create_vertex(x_shft,rbdry[ind],zbdry[ind]) )
        

    cu.cmd("Create Curve Polyline Vertex %d to %d %d"%\
           (verticies[0].id(),verticies[-1].id(), verticies[0].id()))
    curves_end = cu.get_entities('curve')[-1]
    cu.cmd('Delete Vertex All')
    
    # Spin curves around origin
    cu.cmd('Sweep Curve %d to %d Zaxis Angle 360'%(c_0+1, curves_end))
    surf_ids = np.arange(1+s_0,cu.get_entities('surface')[-1]+1,dtype=int).tolist()

    return surf_ids

################################################################################
def __load_boundary_gEqdsk(fname,doPlot=True):
    # Load eqdsk file
    try:
        with open(fname,'r') as f: eqdsk=geqdsk.read(f)
    except Exception as e:
        print(e)
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
def __do_Cut_Ports(surf_ids,s_id_wall):
    R= (41.8)* 0.0254; 
    radial_deg = 4.6144 # degrees for radius/ half width of port
    thicken_depth = 0.00275
    for i in range(10):
        theta_0 = 36*i + 18
        # Build subtraction surface outline
        curves = __make_port_block(i,R,radial_deg,theta_0)
        
        # Subtract from vv wall
        __subtract(curves,surf_ids,theta_0,thicken_depth,s_id_wall)
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
def __subtract(curves,surf_ids,theta_0,thicken_depth,s_id_wall):
    # Build sutraction object
    s1 = cu.create_surface(curves)
    cu.cmd('Project Surface %d Onto Volume %d'%(s1.id(), s_id_wall) ) #13 104
    s1_id  = cu.get_entities('volume')[-1]
    cu.cmd('Thicken Volume %d Depth %f'%(s1_id, thicken_depth))
    
    s1_id  = cu.get_entities('volume')[-1]
    cu.cmd('Volume %d Move %f %f 0'%(s1_id, \
          -thicken_depth*np.cos(theta_0*np.pi/180)/2, -thicken_depth*np.sin(theta_0*np.pi/180)/2) )

    cu.cmd('Subtract Volume %d from Volume %d'%(s1_id,s_id_wall))
    
##########################################################
def __do_Mesh(s_0, id_group,surf_ids, save_Ext):
    
    cu.cmd('delete vertex all')
    cu.cmd('delete curve all')
    
    cu.cmd('imprint body %d to %d'%(s_0+1,cu.get_entities('surface')[-1]))
    cu.cmd('merge body %d to %d'%(s_0+1,cu.get_entities('surface')[-1]))
    
    
    cu.cmd("set trimesher coarse off")
    cu.cmd("set trimesher geometry sizing off")
    cu.cmd("surface all scheme trimesh")
    cu.cmd('Surface All Size 0.1')
    
    cu.cmd("mesh group %d"%id_group)
    
    bl = len(cu.get_entities('block'))
    cu.cmd("set large exodus file on")
    cu.cmd("export genesis 'C_Mod_ThinCurr_VV%s.g' block %d overwrite"%(save_Ext,bl))
    print(f'--- Saved C_Mod_ThinCurr_VV{save_Ext}.g to default Cubit directory ---')
    print(s_0,id_group,surf_ids)
##########################

if __name__ == '__main__': 
     
    build_VV()