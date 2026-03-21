#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 14 09:12:03 2021

@author: kendrick
"""

import sys
import numpy as np

from Classes_Trusses import Node
from Classes_Trusses import Bar
import SectionMaterialConverter as smc



def LoadData(input_geometry,section_file,material_file):
    nodedata = []
    bardata = []
    node_idx = 0
    bar_idx = 0
    nodeflag = False
    barflag = False
    # ensure that the input file is a CSV file
    if(input_geometry.split('.')[-1] !='csv'):
        print("Input must be a csv file. Please input a csv file with file extension .csv included in the end of the input file name.")
        sys.exit()
        
    # create dictionary between list indices and their nodes
    list_idx_to_node = {}
    skipflag = False
    
    # open the file
    with open(input_geometry, 'r') as f:
        # Iterate through all lines
        for line in f:
            # otherwise, split the line
            splitline = line.split();
            commaline = line.split(',')
            if(commaline[0].lower().strip()=='nodes'):
                barflag = False
                nodeflag = True
                continue
            elif(commaline[0].lower().strip()=='beams' or commaline[0].lower().strip()=='bars'):
                barflag = True
                nodeflag = False
                continue
            # Skip headers
            elif(commaline[0].lower().strip()=='index'):
                continue
            
            # node is flagged
            if(nodeflag):
                list_idx = int(commaline[0])
                tempnode = Node(node_idx,list_idx)
                
                tempnode.AddLocation([float(commaline[1]), float(commaline[2])])
                tempnode.AddConstraint(commaline[3])
                tempnode.AddExternalXForce(float(commaline[4]))
                if(commaline[5]==""):
                    tempnode.AddExternalYForce(0)
                else:
                    tempnode.AddExternalYForce(float(commaline[5]))
                
                node_idx += 1
                nodedata.append(tempnode)
                list_idx_to_node.update({list_idx: tempnode})
            elif(barflag):
                if(commaline[0]==""):
                    if skipflag == False:
                        skipflag = True
                        print("skipping line from modified CSV")
                    continue
                init_node_idx = int(commaline[1])
                end_node_idx = int(commaline[2])
                tempbeam = Bar(bar_idx,init_node_idx,end_node_idx)
                
                tempbeam.section_type = commaline[3]
                tempbeam.material_type = commaline[4]
                
                smc.LoadSectionData(tempbeam, tempbeam.section_type, section_file)
                smc.LoadMaterialData(tempbeam, tempbeam.material_type, material_file)        
                
                bar_idx += 1
                bardata.append(tempbeam)
                        
    # print data            
    for bar in bardata:        
        bar.AddInitNode(list_idx_to_node[bar.GetInitNodeListIdx()])
        bar.AddEndNode(list_idx_to_node[bar.GetEndNodeListIdx()])
        
        list_idx_to_node[bar.GetInitNodeListIdx()].AppendToBars(bar)
        list_idx_to_node[bar.GetEndNodeListIdx()].AppendToBars(bar)
    
    return [nodedata, bardata]



