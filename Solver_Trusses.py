#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 14 14:34:19 2021

@author: kendrick
"""

import numpy as np

# compute unknown displacements 
def ComputeDisplacements(K, F, n_unknowns):
    # extract submatrix of unknowns
    K11 = K[0:n_unknowns,0:n_unknowns]
    F1 = F[0:n_unknowns]
    
    d = np.linalg.solve(K11,F1)
    
    return d

# postprocess the forces at known displacement nodes
def PostprocessReactions(K, d, F, n_unknowns, nodes):
    # These are computed net forces and do not
    # take into account external loads applied
    # at these nodes
    F = np.matmul(K[n_unknowns:,0:n_unknowns], d)
    
    # Postprocess the reactions
    for node in nodes:
        if node.xidx >= n_unknowns:
            node.AddReactionXForce(F[node.xidx-n_unknowns][0] - node.xforce_external)
        if node.yidx >= n_unknowns:
            node.AddReactionYForce(F[node.yidx-n_unknowns][0] - node.yforce_external)
        
    return F

# determine internal member loads
def ComputeMemberForces(bars):
    for bar in bars:
        E=bar.E
        A=bar.A
        L=bar.Length()
        lambda_bar = bar.LambdaTerms()
        lambdax=lambda_bar[0]
        lambday=lambda_bar[1]
        near_node = bar.init_node
        far_node = bar.end_node
        near_node_disp = [near_node.xdisp, near_node.ydisp]
        far_node_disp = [far_node.xdisp, far_node.ydisp]
        C=A*E/L
        A=[-lambdax, -lambday, lambdax, lambday]
        B=[near_node_disp[0], near_node_disp[1], far_node_disp[0], far_node_disp[1]]
        bar.axial_load = C*np.dot(A,B)
    
# compute the normal stresses
def ComputeNormalStresses(bars):
    for bar in bars:
        bar.normal_stress = bar.axial_load/bar.A

# compute the critical buckling load of a member
def ComputeBucklingLoad(bars):
    for bar in bars:
        L=bar.Length()*12
        E=bar.E
        I=bar.Iu
        K=1
        P=(np.pi**2)*E*I/(K*L)**2
        bar.buckling_load = P
