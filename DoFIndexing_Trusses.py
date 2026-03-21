#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 14 12:37:32 2021

@author: kendrick
"""

# x constraint is 0, y constraint is 1, moment constraint is 2
def SetNodeIdx(node,constraint_dir, dof_idx):

    if( constraint_dir == 0 ):
        node.SetXIdx(dof_idx)
    elif( constraint_dir == 1 ):
        node.SetYIdx(dof_idx)
    else:
        raise Exception('Invalid index prescribed')
        
def EstablishGlobalDOFNum(nodes):
    dof_idx = 0  
    number_knowns = 0;
    
    for node in nodes:
        constraints = node.ConstraintType()
        if(len(constraints) > 0):
            if(constraints[0]==-1):
                 Exception('Cannot apply the defined constraint on node list index', node.list_idx, ' of type ', node.constraint)
        
        for i in range(0,2):
            if(i in constraints):
                number_knowns += 1
            else:
                SetNodeIdx(node,i,dof_idx)
                dof_idx += 1
            
    number_unknowns = dof_idx
    
    for node in nodes:
        constraints = node.ConstraintType()
        
        for i in constraints:
            SetNodeIdx(node,i, dof_idx)
            dof_idx += 1

    return [number_unknowns, number_knowns]

# Store node displacements from the unknown vector
# if the node was not unknown, set its displacement as zero
def StoreNodeDisplacements(nodes, d, n_unknowns):
    for node in nodes:
        if(node.xidx > n_unknowns-1):
            # set displacement equal to zero
            node.SetXDisplacement(0)
        else:
            # set displacement equal to value in d
            node.SetXDisplacement(d[node.xidx][0])
            
        if(node.yidx > n_unknowns-1):
            # set displacement equal to zero
            node.SetYDisplacement(0)
        else:
            # set displacement equal to value in d
            node.SetYDisplacement(d[node.yidx][0])
    
         
            