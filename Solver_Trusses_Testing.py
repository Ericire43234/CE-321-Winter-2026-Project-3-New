#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb  6 12:21:14 2025

@author: kendrickshepherd
"""

import Main_Trusses as Main
import Solver_Trusses as sol
# import Solver_Trusses_Master as sol

import math
import unittest

class TestTrussSolverOperations(unittest.TestCase):

    def test_Example_3_3_Reactions(self):
        nodes,bars = Main.PlaneTrussStiffness("./csvs/Example_3_3.csv")
        decimal_place = 3
        
        self.assertAlmostEqual(-141.42136, nodes[0].xforce_reaction, decimal_place)
        self.assertAlmostEqual(125.39385, nodes[0].yforce_reaction, decimal_place)
        self.assertAlmostEqual(191.0275, nodes[4].yforce_reaction, decimal_place)

    def test_Example_3_3_Displacement(self):
        nodes, bars = Main.PlaneTrussStiffness("./csvs/Example_3_3.csv")
        decimal_place = 3
        
        # displacements in feet
        self.assertAlmostEqual(0,nodes[0].xdisp,decimal_place)
        self.assertAlmostEqual(0,nodes[0].ydisp,decimal_place)
        self.assertAlmostEqual(0.097,nodes[1].xdisp,decimal_place)
        self.assertAlmostEqual(-0.118,nodes[1].ydisp,decimal_place)
        self.assertAlmostEqual(0.088,nodes[2].xdisp,decimal_place)
        self.assertAlmostEqual(-0.117,nodes[2].ydisp,decimal_place)
        self.assertAlmostEqual(0.086,nodes[3].xdisp,decimal_place)
        self.assertAlmostEqual(-0.113,nodes[3].ydisp,decimal_place)
        self.assertAlmostEqual(0.1785,nodes[4].xdisp,decimal_place)
        self.assertAlmostEqual(0,nodes[4].ydisp,decimal_place)
        self.assertAlmostEqual(0.092,nodes[5].xdisp,decimal_place)
        self.assertAlmostEqual(-0.124,nodes[5].ydisp,decimal_place)
    
    def test_Example_3_3_Forces(self):
        nodes, bars = Main.PlaneTrussStiffness("./csvs/Example_3_3.csv")
        decimal_place = 0

        sol.ComputeMemberForces(bars)
        
        self.assertAlmostEqual(-693,bars[0].axial_load,decimal_place)
        self.assertAlmostEqual(729, bars[1].axial_load,decimal_place)
        self.assertAlmostEqual(-207,bars[2].axial_load,decimal_place)
        self.assertAlmostEqual(-639,bars[3].axial_load,decimal_place)
        self.assertAlmostEqual(-639,bars[4].axial_load,decimal_place)
        self.assertAlmostEqual(729, bars[5].axial_load,decimal_place)
        self.assertAlmostEqual(0, bars[6].axial_load,decimal_place)
        self.assertAlmostEqual(-639, bars[7].axial_load,decimal_place)
        self.assertAlmostEqual(522, bars[8].axial_load,decimal_place)

    def test_Example_3_3_Stresses(self):
        nodes, bars = Main.PlaneTrussStiffness("./csvs/Example_3_3.csv")
        decimal_place = 0

        sol.ComputeMemberForces(bars)
        sol.ComputeNormalStresses(bars)
        
        self.assertAlmostEqual(-42.78,bars[0].normal_stress,decimal_place)
        self.assertAlmostEqual(45.0, bars[1].normal_stress,decimal_place)
        self.assertAlmostEqual(-12.78,bars[2].normal_stress,decimal_place)
        self.assertAlmostEqual(-39.44,bars[3].normal_stress,decimal_place)
        self.assertAlmostEqual(-39.44,bars[4].normal_stress,decimal_place)
        self.assertAlmostEqual(45, bars[5].normal_stress,decimal_place)
        self.assertAlmostEqual(0, bars[6].normal_stress,decimal_place)
        self.assertAlmostEqual(-39.44, bars[7].normal_stress,decimal_place)
        self.assertAlmostEqual(32.22, bars[8].normal_stress,decimal_place)


    def test_Example_3_3_Buckling(self):
        nodes, bars = Main.PlaneTrussStiffness("./csvs/Example_3_3.csv")
        decimal_place = 0

        sol.ComputeMemberForces(bars)
        sol.ComputeBucklingLoad(bars)
        
        self.assertAlmostEqual(833,bars[0].buckling_load,decimal_place)
        self.assertAlmostEqual(669, bars[1].buckling_load,decimal_place)
        self.assertAlmostEqual(9323,bars[2].buckling_load,decimal_place)
        self.assertAlmostEqual(6215,bars[3].buckling_load,decimal_place)
        self.assertAlmostEqual(6215,bars[4].buckling_load,decimal_place)
        self.assertAlmostEqual(4996, bars[5].buckling_load,decimal_place)
        self.assertAlmostEqual(9323, bars[6].buckling_load,decimal_place)
        self.assertAlmostEqual(833,bars[7].buckling_load,decimal_place)
        self.assertAlmostEqual(669, bars[8].buckling_load,decimal_place)



if __name__ == '__main__':
    unittest.main()