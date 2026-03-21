#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 14 08:51:30 2021

@author: kendrick
"""

from ImportCSVData_Trusses import LoadData
from DoFIndexing_Trusses import EstablishGlobalDOFNum
from DoFIndexing_Trusses import StoreNodeDisplacements
from Assembly_Trusses import AssembleStiffness
from Assembly_Trusses import DefineForces
from Solver_Trusses import ComputeDisplacements
from Solver_Trusses import PostprocessReactions
from Solver_Trusses import ComputeMemberForces
from Solver_Trusses import ComputeNormalStresses
from Solver_Trusses import ComputeBucklingLoad

import Plotting_Trusses

def PlaneTrussStiffness( input_geometry):
    
    # load the input data
    [nodes, bars] = LoadData(input_geometry,'aisc_shapes_database_v16_0.csv','Material_Data.csv')
        
    # determine the degrees of freedom
    [n_unknowns,n_knowns] = EstablishGlobalDOFNum(nodes)
    n_matrix = n_unknowns + n_knowns
    
    # assemble the stiffness matrix
    K = AssembleStiffness(bars,n_matrix)
    
    # define the forces acting on the nodes
    F = DefineForces(nodes,n_matrix)
    
    # Compute the unknown displacements
    d = ComputeDisplacements(K, F, n_unknowns)

    # Store the node displacements
    StoreNodeDisplacements(nodes, d, n_unknowns)
    
    # Compute the unknown reactions
    F = PostprocessReactions(K, d, F, n_unknowns, nodes)

    # Compute internal member loads
    ComputeMemberForces(bars)
    
    # Compute normal stresses of members
    ComputeNormalStresses(bars)
    
    # Compute the critical buckling load of the members
    ComputeBucklingLoad(bars)    
    
    # output data for sanity check
    # for node in nodes:
    #     node.Print()
    # for bar in bars:
    #     bar.Print()
    
    # Uncomment these for plotting
    # Plotting_Trusses.PlotStructureData(nodes, bars, "index")
    # Plotting_Trusses.PlotStructureData(nodes, bars, "axial")
    # Plotting_Trusses.PlotStructureData(nodes, bars, "stress")
    # Plotting_Trusses.PlotStructureData(nodes, bars, "disp_in")
    # Plotting_Trusses.PlotStructureData(nodes, bars, "buckling")
    
    return [nodes,bars]


# Run the plane truss function 
[nodes,bars]=PlaneTrussStiffness('Gabled_Howe_6_Panel.csv')
