#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 14 11:25:01 2021

@author: kendrick
"""

import math
import numpy as np

# local stiffness matrix
def LocalStiffnessAssembly(bar):
    # terms used in the stiffness matrix
    A = bar.A
    E = bar.E
    L = bar.Length()
    
    # transformation from local to global coordinate system
    [lambdax, lambday] = bar.LambdaTerms()
    
    # create matrix of zeros and populate
    local_stiffness = np.zeros([4,4])
    
    local_stiffness[0,0] = (A*E/L * lambdax**2)
    local_stiffness[0,1] = A*E/L * lambdax * lambday
    local_stiffness[0,2] = -local_stiffness[0,0]
    local_stiffness[0,3] = -local_stiffness[0,1]
    local_stiffness[1,1] = (A*E/L * lambday**2 )
    local_stiffness[1,2] = -local_stiffness[0,1]
    local_stiffness[1,3] = -local_stiffness[1,1]
    local_stiffness[2,2] = local_stiffness[0,0]
    local_stiffness[2,3] = local_stiffness[0,1]
    local_stiffness[3,3] = local_stiffness[1,1]
    
    # make symmetric
    for i in range(0,4):
        for j in range(i+1,4):
            local_stiffness[j,i] = local_stiffness[i,j]
            
    return local_stiffness

# transform from local stiffness indices to global stiffness indices
def LocalToGlobalIndexing(bar):
    idxs = []
    
    idxs.append(bar.init_node.xidx)
    idxs.append(bar.init_node.yidx)
    
    idxs.append(bar.end_node.xidx)
    idxs.append(bar.end_node.yidx)
    
    return idxs

# Assemble the global stiffness matrix
def AssembleStiffness(bars, n_matrix):
    # this is not efficient and will have lots of zeros generally
    K = np.zeros([n_matrix,n_matrix])
    # iterate through each beam to find local contributions
    for bar in bars:
        # compute the local stiffness information
        k = LocalStiffnessAssembly(bar)
        
        # convert between local and global indexing
        loc_to_glob = LocalToGlobalIndexing(bar)
        
        # again, not efficient
        for i in range(0,4):
            a = loc_to_glob[i]
            for j in range(0,4):
                b = loc_to_glob[j]
                K[a,b] += k[i,j]
                
    return K


# Define global force vectors... some of these will be erroneously populated
#   if the boundary conditions are fixed
def DefineForces(nodes, n_matrix):
    # the force vector (of known applied forces)
    F = np.zeros([n_matrix,1])
    
    for node in nodes:
        F[node.xidx] += node.xforce_external
        F[node.yidx] += node.yforce_external
    
    return F