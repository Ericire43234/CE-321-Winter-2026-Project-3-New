#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 19 14:06:18 2021

@author: kendrick
"""

import math
import numpy as np
import re

EPSILON = 1E-2

# class to keep track of all beam data
class Beam:
    
    def __init__(self, idx):
        self.idx = idx
        self.start = []
        self.end = []
        self.material = ''
        self.section = ''
        self.start_idx = -1
        self.end_idx = -1
        # Local coordinate axes
        self.sdir = None # in plane with udir and rotated 90 degrees
        self.tdir = None # out of plane according to right-hand rule
        self.udir = None # direction from start to end of beam
        self.beam_type = None
    
    def AddDataIdx(self, idx):
        self.idx = idx
        
    def AddMaterial(self, material):
        self.material = material
        
    def AddBeamSection(self, section):
        self.section = section
        
    def AddBeamStart(self, start):
        self.start = start
        
    def AddBeamEnd(self, end):
        self.end = end
        
    def ChangeStartIdx(self,idx):
        self.start_idx = idx
        
    def ChangeEndIdx(self,idx):
        self.end_idx = idx

# class to keep track of all node data      
class Node:
    
    def __init__(self, idx):
        self.idx = idx
        self.location = []
        self.bars = []


# Extract 3d direction from IFCDIRECTION tag
def ExtractDirectionInformation( ifcdirection_input ):
    split_val = ifcdirection_input.split('(')
    if(split_val[0] != 'IFCDIRECTION'):
        Exception('IFCDIRECTION tag expected, but not received')
    else:
        vals = ifcdirection_input.split('((')[1].split('))')[0].split(',')
        return np.array([(float)(vals[0]), (float)(vals[1]), (float)(vals[2])])

def ExtractIFCAxis2Placement3D(data_dictionary,ax2place):
        if(ax2place[0] != 'IFCAXIS2PLACEMENT3D'):
            Exception('IFCAXIS2PLACEMENT3D tag expected, but not received')
        else:
            # extract the origin of the plane of interest
            split_ax2place = ax2place[1].split(')')[0].split(',')
            origin_idx = (int)(split_ax2place[0][1:])
            rel_origin = ExtractIFCCartesianPoint(data_dictionary, origin_idx)
            
            # extract the x-direction information
            rel_y_dir_idx = split_ax2place[1][1:]
            rel_y_dir = []
            if(rel_y_dir_idx == ''):
                rel_y_dir = np.array([0,1,0])
            else:
                rel_y_dir = ExtractDirectionInformation(data_dictionary[(int)(rel_y_dir_idx)])
            
            # extract the x-direction information
            rel_x_dir_idx = split_ax2place[2][1:]
            rel_x_dir = []
            if(rel_x_dir_idx == ''):
                rel_x_dir = np.array([1,0,0])
            else:
                rel_x_dir = ExtractDirectionInformation(data_dictionary[(int)(rel_x_dir_idx)])
        
            rel_z_dir = np.cross(rel_x_dir,rel_y_dir)
            
            return [rel_origin,rel_x_dir,rel_y_dir,rel_z_dir]

def ExtractIFCCartesianPoint(data_dictionary,origin_idx):
    rel_origin_data = data_dictionary[origin_idx].split('((')
    if rel_origin_data[0] != "IFCCARTESIANPOINT":
        Exception("Needs to be a Cartesian point for now")
    else:
        vals = rel_origin_data[1].split('))')[0].split(',')
        rel_origin = [(float)(vals[0]), (float)(vals[1]), (float)(vals[2])]
        return rel_origin


def ExtractNestedPlaneWithOrigin(data_dictionary,local_placement):
    if(local_placement[0] != 'IFCLOCALPLACEMENT'):
        Exception('IFCLOCALPLACEMENT tag expected, but not received')
    else:
        local_placement_data = local_placement[1].split(',')
        local_placement_data[1] = local_placement_data[1].split(')')[0]
        ax2place_idx = (int)(local_placement_data[1][1:]) #index for IFCAXIS2PLACEMENT3D
        ax2place = data_dictionary[ax2place_idx].split('(')

        [rel_origin,rel_x_dir,rel_y_dir,rel_z_dir] = \
            ExtractIFCAxis2Placement3D(data_dictionary, ax2place)
        
        # iterate on progressive local reference frames
        # until global reference frame is found
        if (local_placement[1].split(',')[0][1:] != ''):
            local_placement_idx = (int)(local_placement_data[0][1:])
            local_placement = data_dictionary[local_placement_idx].split('(')
            
            [origin,x_dir,y_dir] = ExtractNestedPlaneWithOrigin(data_dictionary, local_placement)
            
            z_dir = np.cross(x_dir,y_dir)
            # modify relative frame based on the origin
            [rel_origin, rel_x_dir, rel_y_dir, rel_z_dir] = \
                UpdateRelCoordinateSystem(rel_origin,rel_x_dir,rel_y_dir,rel_z_dir, \
                                              origin, x_dir, y_dir, z_dir)
            
        
        # the given frame is in the global coordinate system... return it
        return [rel_origin,rel_x_dir,rel_y_dir]
        
def UpdateRelCoordinateSystem(rel_origin,rel_x_dir,rel_y_dir,rel_z_dir, \
                              origin, x_dir, y_dir, z_dir):
    rel_origin = rel_origin[0]*x_dir + rel_origin[1]*y_dir + rel_origin[2]*z_dir + origin
    rel_x_dir = rel_x_dir[0]*x_dir + rel_x_dir[1]*y_dir + rel_x_dir[2]*z_dir
    rel_y_dir = rel_y_dir[0]*x_dir + rel_y_dir[1]*y_dir + rel_y_dir[2]*z_dir
    rel_z_dir = rel_z_dir[0]*x_dir + rel_z_dir[1]*y_dir + rel_z_dir[2]*z_dir
    return [rel_origin, rel_x_dir, rel_y_dir, rel_z_dir]
            
def ExtractPlaneWithOrigin( data_dictionary, local_place ):    
    [origin,x_dir,y_dir]=ExtractNestedPlaneWithOrigin(data_dictionary,local_place)
    
    return [origin, x_dir, y_dir]

def StrListToFloat(str_list):
    return [float(i) for i in str_list]

# subroutine for extracting start and end point from 3D curve;
#   this belongs to ExtractBeamStartEnd function
def OutputForCurve3D( data_dictionary, shape_rep_idx, origin, x_dir, y_dir):
    shape_data = data_dictionary[shape_rep_idx].split('(',1)
    if(shape_data[0] != 'IFCSHAPEREPRESENTATION'):
        Exception('Arrived at OutputForCurve3D function erroneously (1)')
        
    split_shape_data = shape_data[1].split(',')
    # here we assume that we are in the axis and curve3d regime by construction
    if(split_shape_data[1] != 'Axis' or split_shape_data[2] != 'Curve3D'):
        Exception('Arrived at OutputForCurve3D function erroneously (2)')
    
    trim_idx = (int)(split_shape_data[3].split('))')[0][2:])
    trim = data_dictionary[trim_idx]
    split_trim = trim.split('(',1)
    if(split_trim[0] != 'IFCTRIMMEDCURVE'):
        Exception('IFCTRIMMEDCURVE tag expected, but not received')
    
    split_trim_data = split_trim[1].split(',')
    # TODO this may need to be generalized, but this should work for now
    local_start_idx = (int)(split_trim_data[1].split(')')[0][2:])
    local_start_str = data_dictionary[local_start_idx].split('((')[1].split('))')[0]
    local_start = StrListToFloat(local_start_str.split(','))
    
    local_end_idx = (int)(split_trim_data[2].split(')')[0][2:])
    local_end_str = data_dictionary[local_end_idx].split('((')[1].split('))')[0]
    local_end = StrListToFloat(local_end_str.split(','))
    
    z_dir = np.cross(x_dir,y_dir)
    start_pt = Sum3DPoints(origin, x_dir, y_dir, z_dir, local_start[0], local_start[1], local_start[2])
    end_pt = Sum3DPoints(origin, x_dir, y_dir, z_dir, local_end[0], local_end[1], local_end[2])
    
    axis_along_bar = np.array(end_pt) - np.array(start_pt)
    L = np.linalg.norm(axis_along_bar)
    unitaxis_along_bar = axis_along_bar / np.linalg.norm(axis_along_bar)
    rotate_in_plane_axis = np.array([-unitaxis_along_bar[1],unitaxis_along_bar[0],0])
    out_of_plane = np.cross(unitaxis_along_bar,rotate_in_plane_axis)

    
    return [start_pt, L, rotate_in_plane_axis, out_of_plane, unitaxis_along_bar]

# sum origin with a scaling of the x direction by x_val and scaling of
# the y direction by y_val
def Sum2DPoints(origin, x_dir, y_dir, x_val, y_val):
    xyz = [0,0,0]
    for i in range(0,3):
        xyz[i] = origin[i] + x_val * x_dir[i] + y_val * y_dir[i]
    return xyz

# sum origin with scaling of x,y,z directions by x_val, y_val, and z_val
def Sum3DPoints(origin, x_dir, y_dir, z_dir, x_val, y_val, z_val):
    xyz = [0,0,0]
    for i in range(0,3):
        xyz[i] = origin[i] + x_val * x_dir[i] + y_val * y_dir[i] + z_val * z_dir[i]
    return xyz


def ExtractIFCExtrudedAreaSolid(data_dictionary,shape_data,origin,x_dir,y_dir,z_dir):
# def ExtractIFCExtrudedAreaSolid(data_dictionary,shape_data,rel_origin,rel_x_dir,rel_y_dir,rel_z_dir):
    if(shape_data.split('(')[0]!='IFCEXTRUDEDAREASOLID'):
        Exception("We made some assumptions to get here that have now failed... this code should be revisited")
    else:
        axis_placement_idx = (int)(shape_data.split('(')[1].split(',')[1][1:])
        axis_placement = data_dictionary[axis_placement_idx].split('(',1)
        [rel_origin,rel_x_dir,rel_y_dir,rel_z_dir] = \
            ExtractIFCAxis2Placement3D(data_dictionary,axis_placement)
        # [origin,x_dir,y_dir,z_dir] = \
        #     ExtractIFCAxis2Placement3D(data_dictionary,axis_placement)
        if axis_placement[0] != "IFCAXIS2PLACEMENT3D":
            Exception("Error made in assumptions for the column")
        else:
            
            [rel_origin, rel_x_dir, rel_y_dir, rel_z_dir] = \
                UpdateRelCoordinateSystem(rel_origin,rel_x_dir,rel_y_dir,rel_z_dir, \
                                              origin, x_dir, y_dir, z_dir)

            
            start_pt = rel_origin
            extrude_length = (float)(shape_data.split('(')[1].split(',')[-1].split(')')[0])
            end_pt = start_pt + extrude_length*z_dir
            return [start_pt, extrude_length, x_dir, y_dir, z_dir]

def ExtractIFCShapeRepresentation(data_dictionary, shape_rep_idx, origin, x_dir, y_dir, is_column = False):
    shape_data = data_dictionary[shape_rep_idx].split('(',1)
    if(shape_data[0] != 'IFCSHAPEREPRESENTATION'):
        Exception('IFCSHAPEREPRESENTATION tag expected, but not received')


    split_shape_data = shape_data[1].split(',')
    # this is three-dimensional sweep representation
    if(split_shape_data[1] == 'Body'):
        if(split_shape_data[2] == 'MappedRepresentation'):
            mapped_idx = (int)(split_shape_data[3].split('))')[0][2:])
            ifcitem = data_dictionary[mapped_idx]
            if(ifcitem.split('(')[0] != 'IFCMAPPEDITEM'):
                Exception("IFCMAPPEDITEM tag expected, but not received")
                
            ifcrepmap_idx = (int)(ifcitem.split('(')[1].split(',')[0][1:])
            ifcrepmap = data_dictionary[ifcrepmap_idx]
            
            ifcshaperep_idx = (int)(ifcrepmap.split('(')[1].split(',')[1][1:-3])
            ifcshaperep = data_dictionary[ifcshaperep_idx]
            
            if(ifcshaperep.split('(')[0]!='IFCSHAPEREPRESENTATION'):
                Exception("IFCSHAPEREPRESENTATION tag expected, but not received")

            return ExtractIFCShapeRepresentation(data_dictionary, ifcshaperep_idx, origin, x_dir, y_dir, is_column)

            # shape_rep = ifcshaperep.split('(',1)[1].split('))')[0].split('(')[1].split(',')
            # if(len(shape_rep) > 1):
            #     Exception("We made some assumptions to get here that have now failed... this code should be revisited")
            
            # shape_data = data_dictionary[(int)(shape_rep[0][1:])]

            # if(shape_data.split('(')[0]=='IFCEXTRUDEDAREASOLID'):
            #     z_dir = np.cross(x_dir,y_dir)
            #     return ExtractIFCExtrudedAreaSolid(data_dictionary,shape_data,origin, x_dir, y_dir, z_dir);
                
        elif (split_shape_data[2] == 'SweptSolid'): 
            mapped_idx = (int)(split_shape_data[3].split('))')[0][2:])
            ifcitem = data_dictionary[mapped_idx]
            z_dir = np.cross(x_dir,y_dir)
            return ExtractIFCExtrudedAreaSolid(data_dictionary,ifcitem,origin, x_dir, y_dir, z_dir)
                
    elif(split_shape_data[1] == 'Axis'):

        # for simple curve parameterization
        if(split_shape_data[2] == 'Curve2D'):
            pl_idx = (int)(split_shape_data[3].split('))')[0][2:])
            ifcpl = data_dictionary[pl_idx]
            if(ifcpl.split('(')[0] != 'IFCPOLYLINE'):
                Exception('IFCPOLYLINE tag expected, but not received')
            else:
                coord_idxs = ifcpl.split('((')[1].split('))')[0]
                pt2Dstr = []
                for coord_idx in coord_idxs.split(','):
                    pt2Dstr.append(data_dictionary[(int)(coord_idx[1:])].split('((')[1].split('))')[0])
                start_pt2D = StrListToFloat(pt2Dstr[0].split(','))
                end_pt2D = StrListToFloat(pt2Dstr[-1].split(','))
                
                start_pt = Sum2DPoints(origin, x_dir, y_dir, start_pt2D[0], start_pt2D[1])
                end_pt = Sum2DPoints(origin, x_dir, y_dir, end_pt2D[0], end_pt2D[1])
                
                axis_along_bar = np.array(end_pt) - np.array(start_pt)
                L = np.linalg.norm(axis_along_bar)
                unitaxis_along_bar = axis_along_bar / np.linalg.norm(axis_along_bar)
                rotate_in_plane_axis = np.array([-unitaxis_along_bar[1],unitaxis_along_bar[0],0])
                out_of_plane = np.cross(unitaxis_along_bar,rotate_in_plane_axis)
                
                return [start_pt, L, rotate_in_plane_axis, out_of_plane, unitaxis_along_bar]

        # for 3D trimmed curve 
        elif(split_shape_data[2] == 'MappedRepresentation'):
            mpitem_idx = (int)(split_shape_data[3].split('))')[0][2:])
            mpitem = data_dictionary[mpitem_idx]
            split_mpitem = mpitem.split('(')
            
            if(split_mpitem[0] != 'IFCMAPPEDITEM'):
                Exception('IFCMPAAEDITEM tag expected, but not received')
            
            ifcrepmap_idx = (int)(split_mpitem[1].split(',')[0][1:])
            ifcrepmap = data_dictionary[ifcrepmap_idx]
            split_ifcrepmap = ifcrepmap.split('(')
            
            if(split_ifcrepmap[0] != 'IFCREPRESENTATIONMAP'):
                Exception('IFCREPRESENTATIONMAP tag expected, but not recieved')
            
            ifcshaperep_idx = (int)(split_ifcrepmap[1].split(',')[1].split(')')[0][1:])
            ifcshaperep = data_dictionary[ifcshaperep_idx]
            split_ifcshaperep = ifcshaperep.split('(')
            
            if(split_ifcshaperep[0] != 'IFCSHAPEREPRESENTATION'):
                Exception('IFCSHAPEREPRESENTATION tag expected, but not received')
            
            [start_pt, L, rotate_in_plane_axis, out_of_plane, unitaxis_along_bar] = OutputForCurve3D(data_dictionary, ifcshaperep_idx, origin, x_dir, y_dir)

            return [start_pt, L, rotate_in_plane_axis, out_of_plane, unitaxis_along_bar]

        # for 3d curve
        elif(split_shape_data[3] == 'Curve3D'):
            [start_pt, end_pt] = OutputForCurve3D(data_dictionary, shape_rep_idx, origin, x_dir, y_dir)
            
            return [start_pt, end_pt]
    else:
        Exception('Unknown type definition for IFCSHAPEREPRESENTATION')

def ExtractBeamStartEnd( data_dictionary, shape_idx, origin, x_dir, y_dir, is_column = False):
    split_shape = data_dictionary[shape_idx].split('(',1)
    if(split_shape[0] != 'IFCPRODUCTDEFINITIONSHAPE'):
        Exception('IFCPRODUCTDEFINITIONSHAPE tag expected, but not received')
    
    shape_reps = split_shape[1].split('))')[0].split('(')[1].split(',')
    
    # move all axis representations of curves to the front, where possible
    axis_shape_reps = []
    other_shape_reps = []
    for shape_rep in shape_reps:
        shape_rep_idx = (int)(shape_rep[1:])
        shape_data = data_dictionary[shape_rep_idx].split('(',1)
        if(shape_data[0] != 'IFCSHAPEREPRESENTATION'):
            Exception('IFCSHAPEREPRESENTATION tag expected, but not received')
        
        split_shape_data = shape_data[1].split(',')
        if(split_shape_data[1] == 'Axis'):
            axis_shape_reps.append(shape_rep)
        else:
            other_shape_reps.append(shape_rep)
        
    shifted_shape_reps = axis_shape_reps + other_shape_reps
    
    for shape_rep in shifted_shape_reps:
        shape_rep_idx = (int)(shape_rep[1:])
        vals = ExtractIFCShapeRepresentation(data_dictionary, shape_rep_idx, origin, x_dir, y_dir, is_column)
        if vals != None:
            return vals
    
# Test if two nodes are equal within some tolerance
# this is using the one-norm, which is equivalent ot the two-norm
def EqualPositions(pos1, pos2):
    if len(pos1) != len(pos2):
        Exception('The dimensions of the positions differ; please uniformize dimension')
    
    equal_nodes = True
    tol = EPSILON
    for i in range(0,3):
        if abs(pos1[i]-pos2[i]) > tol:
            equal_nodes = False
            break
    
    return equal_nodes

def OneNormDist(pos1, pos2):
    dist = 0
    for i in range(0,3):
        dist = dist + abs(pos1[i]-pos2[i])

    return dist

def EqualNodeAndPosition(node, pos):
    return EqualPositions(node.location, pos)

# Add a node to the list of nodes if it is not yet present
def EnterNodeIfNecessary(nodes, potential_node):
    same_node_bool = []
    for i in range(0,len(nodes)):
         same_node_bool.append(EqualNodeAndPosition(nodes[i],potential_node))
    if True not in same_node_bool:
         node = Node(len(nodes))
         node.location = potential_node
         nodes.append(node)
         return

# parameterize a line from start point to end point as (a,b,c) and (d,e,f)
# take the input point as (g,h,i)
# parameterize line segment from start to end as 
# [a + (d-a)t, b+ (e-b)t, c + (f-c)t]; take the dot product with point and set equal to zero         
# return the point after t is calculated
# see https://mathworld.wolfram.com/Point-LineDistance3-Dimensional.html
def ClosestPointOnLine(line_start,line_end,pt):
    a = line_start[0]
    b = line_start[1]
    c = line_start[2]
    d = line_end[0]
    e = line_end[1]
    f = line_end[2]
    g = pt[0]
    h = pt[1]
    i = pt[2]
 
    denom = (d-a)**2 + (e-b)**2 + (f-c)**2
    t = -((a - g)*(d - a) + (b - h)*(e - b) + (c - i)*(f - c))/denom
#    t = (g*a + b*h + c*i) / (g*(a-d) + h*(b-e) + i*(c-f))
    
    return [[a + (d-a)*t, b + (e-b)*t, c + (f-c)*t],t]

def InClosure(tval):
    if tval >= -EPSILON and tval <= 1+EPSILON:
        return True
    else:
        return False

def IntersectsLineSegment(line_start, line_end, pt):
    # find the closest point on the line segment and the corresponding t value
    [closest,tval] = ClosestPointOnLine(line_start, line_end, pt)
    # determine if that is in the closure of the line segment 
    return EqualPositions(closest, pt) and InClosure(tval)
        

# Function to sort the list of tuples by its second item
def Sort_Tuple(tup): 
      
    # getting length of list of tuples
    lst = len(tup) 
    for i in range(0, lst): 
          
        for j in range(0, lst-i-1): 
            if (tup[j][1] > tup[j + 1][1]): 
                temp = tup[j] 
                tup[j]= tup[j + 1] 
                tup[j + 1]= temp 
    return tup 

# Find the nearest point on a beam to a specified point
# If this point and the nearest point are within a tolerance of one another,
# split the beam at a prescribed set of nodes
def SplitBeamsAtNodes(nodes,beam_dict):
    #TODO change this to a vector-matrix operation
    new_beam_dict = {}
    counter = 0
    for key in beam_dict:
        beam = beam_dict[key]
        # list of tuples of nodes and lengths from start
        interior_nodes = []
        # iterate through all nodes and find any that intersect in the interior of the beam
        for i in range(0, len(nodes)):
            if IntersectsLineSegment(beam.start, beam.end, nodes[i].location):
                lenfromstart = OneNormDist(beam.start, nodes[i].location)
                interior_nodes.append( (nodes[i], lenfromstart) )
        
        # Sort the list of tuples by distance from start node
        iter_nodes = Sort_Tuple(interior_nodes)

        l = len(iter_nodes)        
        for i in range(1, l):
            # determine start and end nodes
            beam_start = iter_nodes[i-1][0]
            beam_end = iter_nodes[i][0]
            
            # populate data in beams
            new_beam = Beam(counter)
            new_beam.AddMaterial(beam.material)
            new_beam.AddBeamSection(beam.section)
            new_beam.AddBeamStart(beam_start.location)
            new_beam.AddBeamEnd(beam_end.location)
            new_beam.ChangeStartIdx(beam_start.idx)
            new_beam.ChangeEndIdx(beam_end.idx)
            new_beam.sdir = beam.sdir
            new_beam.tdir = beam.tdir
            new_beam.udir = beam.udir

            # populate connectivity in nodes
            beam_start.bars.append(counter)
            beam_end.bars.append(counter)
            
            new_beam_dict[counter] = new_beam
            
            counter = counter + 1

                    
        
    return new_beam_dict

def FloatToZero(f):
    if abs(f) < EPSILON:
        return 0.
    else:
        return f

def OutputAsSTEP(nodes, beams, filename):
    stpfile = filename + ".stp"
    with open(stpfile, 'w') as file:
        file.write('ISO-10303-21;\n');
        file.write('HEADER;\n');
        file.write('/* Generated by Kendrick Shepherd\n')
        file.write(' */\n')
        file.write("/* OPTION: using custom schema-name function */\n")
        file.write('\n')
        file.write('FILE_DESCRIPTION(\n')
        file.write("/* description */ ('Output from IFC converter'),'');\n")
        file.write('\n')
        file.write('FILE_NAME(\n')
        file.write('/* name */ ' + "'" + filename + "'," + '\n')
        file.write('/* time_stamp */ ' + "'" + "',\n")
        file.write('/* author */ ' + "(''),\n")
        file.write("/* organization */ (''),\n")
        file.write("/* preprocessor_version */ '',\n")
        file.write("/* originating_system */ '',\n")
        file.write("/* aurhorisation */ '');\n")
        file.write("\n")
        file.write("FILE_SCHEMA (('AUTOMOTIVE_DESIGN'))\n")
        file.write("ENDSEC;\n")
        file.write("\n")
        file.write("DATA;\n")
        file.write("#10=SHAPE_DEFINITION_REPRESENTATION(#11,#31);\n")
        file.write("#11=PRODUCT_DEFINITION_SHAPE('Document','',#13);\n")
        file.write("#12=PRODUCT_DEFINITION_CONTEXT('3D Mechanical Parts',#17,'design');\n")
        file.write("#13=PRODUCT_DEFINITION('A','First version',#14,#12);\n")
        file.write("#14=PRODUCT_DEFINITION_FORMATION_WITH_SPECIFIED_SOURCE('A',\n")
        file.write("'First version',#19,.MADE.);\n")
        file.write("#15=PRODUCT_RELATED_PRODUCT_CATEGORY('tool','tool',(#19));\n")
        file.write("#16=APPLICATION_PROTOCOL_DEFINITION('Draft International Standard',\n")
        file.write("'automotive_design',1999,#17);\n")
        file.write("#17=APPLICATION_CONTEXT(\n")
        file.write("'data for automotive mechanical design processes');\n")
        file.write("#18=PRODUCT_CONTEXT('3D Mechanical Parts',#17,'mechanical');\n")
        file.write("#19=PRODUCT('Document','Document','Rhino converted to STEP',(#18));\n")
        file.write("#20=(\n")
        file.write("LENGTH_UNIT()\n")
        file.write("NAMED_UNIT(*)\n")
        file.write("SI_UNIT($,.METRE.)\n")
        file.write(");\n")
        file.write("#21=LENGTH_MEASURE_WITH_UNIT(LENGTH_MEASURE(0.3048),#20);\n")
        file.write("#22=(\n")
        file.write("CONVERSION_BASED_UNIT('FEET',#21)\n")
        file.write("LENGTH_UNIT()\n")
        file.write("NAMED_UNIT(#25)\n")
        file.write(");\n")
        file.write("#23=(\n")
        file.write("NAMED_UNIT(*)\n")
        file.write("PLANE_ANGLE_UNIT()\n")
        file.write("SI_UNIT($,.RADIAN.)\n")
        file.write(");\n")
        file.write("#24=DIMENSIONAL_EXPONENTS(0.,0.,0.,0.,0.,0.,0.);\n")
        file.write("#25=DIMENSIONAL_EXPONENTS(1.,0.,0.,0.,0.,0.,0.);\n")
        file.write("#26=PLANE_ANGLE_MEASURE_WITH_UNIT(PLANE_ANGLE_MEASURE(0.01745329252),#23);\n")
        file.write("#27=(\n")
        file.write("CONVERSION_BASED_UNIT('DEGREES',#26)\n")
        file.write("NAMED_UNIT(#24)\n")
        file.write("PLANE_ANGLE_UNIT()\n")
        file.write(");\n")
        file.write("#28=(\n")
        file.write("NAMED_UNIT(*)\n")
        file.write("SI_UNIT($,.STERADIAN.)\n")
        file.write("SOLID_ANGLE_UNIT()\n")
        file.write(");\n")
        file.write("#29=UNCERTAINTY_MEASURE_WITH_UNIT(LENGTH_MEASURE(0.01),#22,\n")
        file.write("'DISTANCE_ACCURACY_VALUE',\n")
        file.write("'Maximum model space distance between geometric entities at asserted c\n")
        file.write("onnectivities');\n")
        file.write("#30=(\n")
        file.write("GEOMETRIC_REPRESENTATION_CONTEXT(3)\n")
        file.write("GLOBAL_UNCERTAINTY_ASSIGNED_CONTEXT((#29))\n")
        file.write("GLOBAL_UNIT_ASSIGNED_CONTEXT((#28,#27,#22))\n")
        file.write("REPRESENTATION_CONTEXT('ID1','3D')\n")
        file.write(");\n")
        file.write("#31=SHAPE_REPRESENTATION('Document',(#32,#32),#30);\n")
        file.write("#32=AXIS2_PLACEMENT_3D('',#35,#33,#34);\n")
        file.write("#33=DIRECTION('',(0.,0.,1.));\n")
        file.write("#34=DIRECTION('',(1.,0.,0.));\n")
        file.write("#35=CARTESIAN_POINT('',(0.,0.,0.));\n")
        
        # Now begin to add all of the nodes
        node_dict = {}
        counter = 36
        for i in range(0,len(nodes)):
            node_dict[i] = '#' + (str)(counter)
            file.write(node_dict[i] + "=CARTESIAN_POINT('',(" + \
                       (str)(FloatToZero(nodes[i].location[0])) + "," + \
                       (str)(FloatToZero(nodes[i].location[1])) + "," + \
                       (str)(FloatToZero(nodes[i].location[2])) + "));\n")
            counter = counter + 1
        
        for i in range(0,len(nodes)):
            file.write("#" + (str)(counter) + "=PRESENTATION_LAYER_ASSIGNMENT('Default','',(")
            file.write(node_dict[i])
            file.write("));\n")  
            counter = counter+1
        
        # next, add all of the beams
        beam_to_hash = {}
        for key in beams:
            beam = beams[key]
            end_loc = nodes[beam.end_idx].location
            start_loc = nodes[beam.start_idx].location
            direction = [end_loc[0] - start_loc[0], \
                         end_loc[1] - start_loc[1], \
                         end_loc[2] - start_loc[2]]
            length = math.sqrt(direction[0]**2 + direction[1]**2 + direction[2]**2)
            normalized = [direction[0] / length, direction[1]/ length, direction[2] / length]
            file.write("#" + (str)(counter) + "=DIRECTION('',(" + 
                       (str)(FloatToZero(normalized[0])) + "," + \
                       (str)(FloatToZero(normalized[1])) + "," + \
                       (str)(FloatToZero(normalized[2])) + "));\n")
            file.write("#" + (str)(counter + 1) + "=VECTOR('',#" + \
                       (str)(counter) + "," + \
                       (str)(length) + ");\n")
            file.write("#" + (str)(counter + 2) + "=LINE(''," + \
                       node_dict[beam.start_idx] + ",#" +
                       (str)(counter + 1) + ");\n")
            beam_to_hash[key] = '#' + (str)(counter + 2)
            
            file.write("#" + (str)(counter+3) + "=PRESENTATION_LAYER_ASSIGNMENT('Default','',(")
            file.write(beam_to_hash[key])
            file.write("));\n")  
                
            counter = counter + 4
        
        file.write("#" + (str)(counter) + "=GEOMETRIC_CURVE_SET('curve_set_0',(")
        for i in range(0,len(nodes)):
            file.write(node_dict[i])
            #if i != len(nodes)-1:
            file.write(",")
            #else:
        keys = list(beam_to_hash)
        for i in range(0,len(keys)):
            file.write(beam_to_hash[keys[i]])
            if i != len(keys) - 1:
                file.write(",")
            else:
                file.write("));\n")
        crv_set_idx = counter
        
        
        counter = counter + 1
        file.write("#" + (str)(counter) + "=SHAPE_REPRESENTATION_RELATIONSHIP('','',#31,#" + (str)(counter+1) + ");\n")
        counter = counter + 1
        file.write("#" + (str)(counter) + "=GEOMETRICALLY_BOUNDED_WIREFRAME_SHAPE_REPRESENTATION(\n")
        file.write("'wireframe_rep_0',(#" + (str)(crv_set_idx) + ",#32),#30);\n")
        file.write("ENDSEC;\n")
        file.write("END-ISO-10303-21;\n")
        
        
        
        
# simplify to a planar structure
def OutputNodeCSV2D(file, nodes):
    file.write("Nodes \n")
    file.write("Index,XCoord(ft),YCoord(ft),Constraint,XForce(kip),YForce(kip),BeamIdxs\n")
    
    # determine the fixed plane (x, y, or z)
    samedir = [True, True, True]
    for i in range(1,len(nodes)):
        for j in range(0,3):
            if samedir[j]:
                if abs(nodes[0].location[j] - nodes[i].location[j]) > EPSILON:
                    samedir[j] = False

    dirs = []
    for j in range(0,3):
        if samedir[j] == False:
            dirs.append(j)
    
    if len(dirs) > 2:
        Exception("The input object is not planar in one of the three primary directions")
    elif len(dirs) == 1:
        if(dirs[0]==0):
            dirs.append(1)
        else:
            dirs.insert(0,0) # input 0 to the front of the list
    
    for i in range(0,len(nodes)):
        file.write((str)(nodes[i].idx) + "," + (str)(nodes[i].location[dirs[0]]) + "," + (str)(nodes[i].location[dirs[1]]) + ",,0,0,")
        for j in range(0,len(nodes[i].bars)):
            if isinstance(nodes[i].bars[j], int):
                file.write((str)(nodes[i].bars[j]))
            else:
                file.write((str)(nodes[i].bars[j].idx))
            if j != len(nodes[i].bars)-1:
                file.write(";")
            else:
                file.write("\n")

def OutputNodeCSV3D(file, nodes):
    file.write("Nodes\n")
    file.write("Index,XCoord,YCoord,ZCoord,Constraint,XForce,YForce,ZForce,XMoment,YMoment,ZMoment,BeamIdxs \n")
    for i in range(0,len(nodes)):
        file.write((str)(nodes[i].idx) + "," + (str)(nodes[i].location[0]) + "," + (str)(nodes[i].location[1]) + "," + (str)(nodes[i].location[2]) + ",,0,0,0,0,0,0,")
        for j in range(0,len(nodes[i].bars)):
            file.write((str)(nodes[i].bars[j]))
            if j != len(nodes[i].bars)-1:
                file.write(";")
            else:
                file.write("\n")

def OutputAsCSV(csvfile,nodes,beam_data,two_dimensions):
    with open(csvfile, "w") as file:
        if two_dimensions:
            OutputNodeCSV2D(file, nodes)
        else:
            OutputNodeCSV3D(file, nodes)
    
        file.write("Beams\n")
        file.write("Index,Start Node,End Node,Section Type,Material,Sdir,Tdir,Udir\n")
        if type(beam_data) is dict:
            for key in beam_data:
                file.write((str)(beam_data[key].idx) + "," + \
                           (str)(beam_data[key].start_idx) + "," + \
                           (str)(beam_data[key].end_idx) + "," + \
                           (str)(beam_data[key].section) + "," + \
                           (str)(beam_data[key].material) + "," + \
                           (str)(beam_data[key].sdir) + "," + \
                           (str)(beam_data[key].tdir) + "," + \
                           (str)(beam_data[key].udir) + "\n")
        else:
            # this is actually a beam from a different class...
            for beam in beam_data:
                file.write((str)(beam.idx) + "," + \
                           (str)(beam.init_node.idx) + "," + \
                           (str)(beam.end_node.idx) + "," + \
                           (str)(beam.section_type) + "," + \
                           (str)(beam.material_type) + "," + \
                           (str)(beam.sdir) + "," + \
                           (str)(beam.tdir) + "," + \
                           (str)(beam.udir) + "\n")


def AddIfBeam( data_dictionary, beam_dict, i, rel_origin, rel_x_dir, rel_y_dir, rel_z_dir ):
    if(i in data_dictionary and i not in beam_dict):
        val = data_dictionary[i]
        split_val = val.split('(',1) # only split at first occurence
        # check if the index is a beam or other member of the ifc
        if(split_val[0] == 'IFCBEAM' or \
           split_val[0] == 'IFCMEMBER' or \
           split_val[0] == 'IFCCOLUMN'):
            
            # create new indexed beam for the beam dictionary
            temp_beam = Beam(i)
            beam_data = split_val[1].split(',')
            # add cross section data to the list
            temp_beam.AddBeamSection(beam_data[4])
            
            # address the geometry data
            # extract local origin data
            local_place_idx = (int)(beam_data[5][1:]) # extract the index for IFCLOCALPLACEMENT
            local_place = data_dictionary[local_place_idx].split('(')

            [origin, x_dir, y_dir] = \
                ExtractPlaneWithOrigin( data_dictionary, local_place)
                                   
            z_dir = np.cross(x_dir,y_dir)
            
            [rel_origin, rel_x_dir, rel_y_dir, rel_z_dir] = \
                UpdateRelCoordinateSystem(rel_origin,rel_x_dir,rel_y_dir,rel_z_dir, \
                                              origin, x_dir, y_dir, z_dir)

            
            # Extract beam positions using local geometric data plus
            # the new plane information above
            idx = (int)(beam_data[6][1:])
            [start_pt, L, local_x_dir, local_y_dir, local_z_dir] = ExtractBeamStartEnd( data_dictionary, idx, rel_origin, rel_x_dir,rel_y_dir, split_val[0] == 'IFCCOLUMN')

            end_pt = start_pt + L*local_z_dir
            temp_beam.AddBeamStart(start_pt)
            temp_beam.AddBeamEnd(end_pt)
            temp_beam.udir = local_z_dir
            temp_beam.sdir = local_x_dir
            temp_beam.tdir = local_y_dir
            
            # store ifc stuff
            temp_beam.beam_type = split_val[0]
            
            # add to the beam dictionary
            beam_dict[i] = temp_beam
            
        elif(split_val[0] == 'IFCRELASSOCIATESMATERIAL'):
            temp_data = split_val[1].split('(')[1].split(')')
            idxs = temp_data[0]
            material_idx = (int)(temp_data[1][2:])
            for hash_idx in idxs.split(','):
                idx = (int)(hash_idx[1:])
                if(idx not in beam_dict):
                    Exception('The proposed beam has not yet been found; add the beam before adding its material')
                else:
                    material = data_dictionary[material_idx]
                    beam_dict[idx].AddMaterial(material.split('(')[1].split(')')[0])

# move the beams up or down to be on their corresponding storey
def AdjustBeamsToLevel(data_dictionary,beam_dict,last_int):
    for i in range(0,last_int):
        if (i in data_dictionary):
            val = data_dictionary[i]
            split_val = val.split('(',1) # only split at first occurence
            if split_val[0] == "IFCRELCONTAINEDINSPATIALSTRUCTURE":
                split_data = split_val[1].split('(')[1].split(')')[0].split(',')
                storeyidx = int(split_val[1].split(',')[-1].split(')')[0][1:])
                storey = data_dictionary[storeyidx]
                if(storey.split('(',1)[0] != "IFCBUILDINGSTOREY"):
                    Exception('IFCBUILDINGSTOREY was expected but not found')
                local_placement_idx = int(storey.split(",")[5][1:])            
                local_placement = data_dictionary[local_placement_idx].split('(')
                
                [origin,x_dir,y_dir] = ExtractNestedPlaneWithOrigin(data_dictionary, local_placement)
                
                z_dir = np.cross(x_dir,y_dir)
                
                for datum in split_data:
                    idx = int(datum[1:])
                    if idx in beam_dict:
                        beam_dict[idx].start += origin
                        beam_dict[idx].end += origin
            
            


# This program reads an IFC file and digests it into a set of beams with 
# cross-sectional data and material information
# This can then be used as input for a finite element solve
def IFC_Reader( input_ifc, output_filename, two_dimensions=True  ):
    
    data_dictionary = {}
    last_int = 0
    # ensure that the input is an ifc file
    filename = input_ifc.split('.')[0]
    if(input_ifc.split('.')[-1].lower() != 'ifc'):
        Exception('The input file was not an ifc file; try including the file extension or checking the input file again.')
    else:
        # open the file
        with open(input_ifc, 'r', encoding="utf8") as f:
            # Iterate through all lines
            for line in f:

                # store data starting with a
                if(line[0]=='#'):
                   split_str = re.split('= |=',line)
                   key = (int)(split_str[0][1:])
                   data_dictionary[key]= split_str[1].replace("'","")
                   last_int = key
                   
        beam_dict = {}
        # beam_elem_list = []
        # # iterate through element assemblies and then through
        # # isolated members
        # last_int = last_int + 1
        # for i in range(0,last_int):
        #     if(i in data_dictionary):
        #         val = data_dictionary[i]
        #         split_val = val.split('(',1) # only split at first occurence
        #         # check if the index is a beam or other member of the ifc
        #         if(split_val[0] == 'IFCRELAGGREGATES'):
        #             resplit = split_val[1].split('(')
        #             agg_elem_idx = resplit[0].split(',')[4][1:]
        #             if agg_elem_idx != "":
        #                 agg_elem_split = data_dictionary[(int)(agg_elem_idx)].split('(',1)
        #                 if agg_elem_split[0] == 'IFCELEMENTASSEMBLY':
        #                     beam_elem_str = resplit[1].split(')')[0]
        #                     beam_elem_list = [(int)(val[1:]) for val in beam_elem_str.split(',')]
        #                     beam_location_idx = agg_elem_split[1].split(',')[5][1:]
        #                     if beam_location_idx != "":
        #                         local_place = data_dictionary[(int)(beam_location_idx)].split('(')
        #                         [origin, x_dir, y_dir] = \
        #                            ExtractPlaneWithOrigin( data_dictionary, local_place)
        #                         z_dir = np.cross(x_dir,y_dir)
        #                     else:
        #                         origin = np.array([0,0,0])
        #                         x_dir = np.array([1,0,0])
        #                         y_dir = np.array([0,1,0])
        #                         z_dir = np.array([0,0,1])

        #                     for val in beam_elem_list:
        #                         AddIfBeam(data_dictionary, beam_dict, val, origin, x_dir, y_dir, z_dir)
        #                 else:
        #                     pass
        #             else:
        #                 pass
        #         else:
        #             pass

        
        origin = np.array([0,0,0])
        x_dir = np.array([1,0,0])
        y_dir = np.array([0,1,0])
        z_dir = np.array([0,0,1])
        
        last_int = last_int + 1
        for i in range(0,last_int):
            AddIfBeam(data_dictionary, beam_dict, i, origin, x_dir, y_dir, z_dir)
            
        # modify based on stories that the objects are on
        # AdjustBeamsToLevel(data_dictionary,beam_dict,last_int)
        
        nodes = []
        for key in beam_dict:
            if len(nodes) == 0:
                node = Node(0)
                node.location = beam_dict[key].start
                nodes.append(node)
            
            EnterNodeIfNecessary(nodes, beam_dict[key].start)
            EnterNodeIfNecessary(nodes, beam_dict[key].end)
          
        new_beam_dict = SplitBeamsAtNodes(nodes, beam_dict)
        
        # output as a CSV file... works if the file name already
        # includes .csv or does not
        csvfile = output_filename.split(".csv")[0] + ".csv"
        OutputAsCSV(csvfile,nodes,new_beam_dict,two_dimensions)
       
        # output as a STEP file
        #OutputAsSTEP(nodes, new_beam_dict, filename)
        
        for key in beam_dict:
            print((str)(beam_dict[key].idx) + " " + (str)(beam_dict[key].section) + " " + (str)(beam_dict[key].material))
            print(beam_dict[key].start)
            print(beam_dict[key].end)
            print('')
