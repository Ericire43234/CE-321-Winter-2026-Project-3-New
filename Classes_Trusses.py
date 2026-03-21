#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 14 11:10:25 2021

@author: kendrick
"""
import math
import sys
import copy
import numpy as np

# Node member information
class Node:
    
    def __init__(self, idx, list_idx):
        # index of the node for this program
        self.idx = idx
        # index of the node in the CSV file
        self.__list_idx = list_idx
        self.location = []
        self.constraint = 'none'
        self.xforce_external = 0
        self.yforce_external = 0
        self.zmoment_external = 0
        self.xforce_reaction = float("NAN")
        self.yforce_reaction = float("NAN")
        self.zmoment_reaction = float("NAN")
        self.xdisp = math.nan
        self.ydisp = math.nan
        self.zrotate = math.nan
        self.bars = []
        self.xidxdof = -1
        self.yidxdof = -1
        self.rotzidxdof = -1
                       
    def AddLocation(self, location):
        self.location = location
        
    def AddConstraint(self, constraint):
        self.constraint = constraint
    
    def AddExternalXForce(self, xforce):
        self.xforce_external = xforce
        
    def AddExternalYForce(self, yforce):
        self.yforce_external = yforce
        
    def HasXReactionForce(self):
        return 0 in self.ConstraintType()
    
    def HasYReactionForce(self):
        return 1 in self.ConstraintType()

    def AddReactionXForce(self, xforce):
        if(self.HasXReactionForce()):
            self.xforce_reaction = xforce
        else:
            sys.exit("Cannot append reaction force in x when constraint %s cannot support it" % self.constraint)
        
    def AddReactionYForce(self, yforce):
        if(self.HasYReactionForce()):
            self.yforce_reaction = yforce
        else:
            sys.exit("Cannot append reaction force in y when constraint %s cannot support it" % self.constraint)
            
    def SetXDisplacement(self, xdisp):
        self.xdisp = xdisp
            
    def SetYDisplacement(self, ydisp):
        self.ydisp = ydisp

    def AppendToBars(self, beam):
        self.bars.append(beam)
        
    def SetXIdx(self, idx):
        self.xidx = idx
        
    def SetYIdx(self, idx):
        self.yidx = idx
        
    def IsRollerConstrainedInX(self):
        return self.constraint.lower()=="xdisp" \
            or self.constraint.lower()=="roller_no_xdisp"

    def IsRollerConstrainedInY(self):
        return self.constraint=="ydisp" \
            or self.constraint=="roller_no_ydisp"
        
    def ConstraintType(self):
        # -1 if incompatible, 0 if x, 1 if y, 2 if moment
        if(self.constraint.lower() == 'none' or self.constraint.lower() == ''):
            return []
        elif(self.IsRollerConstrainedInX()):
            return [0]
        elif(self.IsRollerConstrainedInY()):
            return [1]
        elif(self.constraint.lower() == 'pin'):
            return [0,1]
        elif(self.constraint.lower() == 'fixed'):
            return [0,1,2]
        else: # the current constraint type is not defined
            sys.exit("The current type of constraint is not defined")
    
    def GetNetXForce(self):
        if(0 in self.ConstraintType() and np.isnan(self.xforce_reaction)):
            sys.exit("Cannot compute net x force without resolved x reaction force")
        else:
            if(0 in self.ConstraintType()):
                return self.xforce_external + self.xforce_reaction
            else:
                return self.xforce_external
    
    def GetNetYForce(self):
        if(1 in self.ConstraintType() and np.isnan(self.yforce_reaction)):
            sys.exit("Cannot compute net y force without resolved y reaction force")
        else:
            if(1 in self.ConstraintType()):
                return self.yforce_external + self.yforce_reaction
            else:
                return self.yforce_external

    def GetNetZMoment(self):
        if(2 in self.ConstraintType() and np.isnan(self.zmoment_reaction)):
            sys.exit("Cannot compute net z moment without resolved z reaction moment")
        else:
            if(2 in self.ConstraintType()):
                return self.zmoment_external + self.zmoment_reaction
            else:
                return self.zmoment_external



    
    def Print(self):
        print('NodeIdx = ', self.idx)
        # print('CSVIdx = ', self.__list_idx)
        # print('Location = ', self.location)
        # print('Constraint = ', self.constraint)
        # print('External X Force = ', self.xforce_external)
        # print('External Y Force = ', self.yforce_external)
        if(0 in self.ConstraintType()):
            print('Reaction X Force = ', self.xforce_reaction)
        if(1 in self.ConstraintType()):
            print('Reaction Y Force = ', self.yforce_reaction)
        # print('Unknown X Index = ', self.xidx)
        # print('Unknown Y Index = ', self.yidx)
        print('Disp X = ', self.xdisp)
        print('Disp Y = ', self.ydisp)
        print('')
    
    def SquaredDistTweenNodes(self,other):
        dist = 0;
        for i in range(0,len(self.location)):
            dist += (other.location[i]-self.location[i])**2
        return dist
    
    def Clone(self):
        return copy.deepcopy(self)

# Beam member information
class Bar:
    
    def __init__(self, idx,init_node_idx,end_node_idx):
        self.idx = idx
        self.E = 0
        self.It = 0 # strong axis
        self.A = 0
        self.Iu = 0 # weak axis
        self.axial_load = float("NAN")
        self.normal_stress = float("NAN")
        self.buckling_load = float("NAN")
        self.__init_node_list_idx = init_node_idx
        self.__end_node_list_idx = end_node_idx
        self.init_node = Node(-1,-1)
        self.end_node = Node(-1,-1)
        self.section_type = ""
        self.material_type = ""
        self.self_weight = 0
        self.is_computed = False
        self.is_column = False
        
        
    # length of the beam
    def Length(self):
        init_location = self.init_node.location
        end_location = self.end_node.location
        
        deltas = []
        for i in range(0,len(end_location)):
            deltas.append(end_location[i]-init_location[i])
                
        beam_len = np.linalg.norm(deltas)
        return beam_len

    # transformation terms from local beam coordinate system to global x, y 
    #   coordinate system
    def LambdaTerms(self):
        init_location = self.init_node.location
        end_location = self.end_node.location
        
        deltax = end_location[0] - init_location[0]
        deltay = end_location[1] - init_location[1]
        
        bar_len = self.Length()
        
        lambdax = deltax / bar_len
        lambday = deltay / bar_len
        
        return [lambdax, lambday]
                
    def AddYoungsModulus(self, E):
        self.E = E

    def GetStrongSecondMoment(self):
        return self.It

    def GetWeakSecondMoment(self):
        return self.Iu
    
    def AddArea(self, A):
        self.A = A
        
    def AddInitNode(self, init_node):
        self.init_node = init_node
        
    def AddEndNode(self, end_node):
        self.end_node = end_node
        
    def AddSelfWeight(self, w):
        self.self_weight = w
        
    def GetMidpoint(self):
        pos = []
        for i in range(0,len(self.init_node.location)):
            pos.append((self.init_node.location[i]+self.end_node.location[i])/2)
        return np.array(pos)
            
    # get index of the initial node (from the CSV)
    # DO NOT USE unless you know what you are doing
    def GetInitNodeListIdx(self):
        return self.__init_node_list_idx
    # get index of the end node (from the CSV)
    # DO NOT USE unless you know what you are doing
    def GetEndNodeListIdx(self):
        return self.__end_node_list_idx
    
    def Print(self):
        print('BarIdx = ', self.idx)
        # print('ListIdx Nodes = ', self.__init_node_list_idx, ', ', self.__end_node_list_idx)
        # print('Modulus = ', self.E)
        # print('Second Moment of Inertia = ', self.I)
        # print('Area = ', self.A)
        print('Axial load is ', self.axial_load)
        print('Normal stress is ', self.normal_stress )
        print('Critical buckling load is ', self.buckling_load )
        print('')
        
    def BarToVector(self):
        init_loc = np.array(self.init_node.location)
        end_loc = np.array(self.end_node.location)
        return end_loc - init_loc        
            
    def Clone(self):
        return copy.deepcopy(self)
