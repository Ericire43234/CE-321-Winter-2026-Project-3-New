#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov  2 14:10:02 2021

@author: kendrickshepherd
"""

import sys

# Exchange data from being material to modulus of elasticity
def LoadMaterialData(bar, material, material_file = ""):   
    if material_file == "":
        bar.E = float(material)
    else:
        data_found = False
        data_line = None
        title_line = None
        with open(material_file, 'r') as file:
            is_top = True
            for line in file:
                if is_top:
                    title_line = line.strip().lower().split(",")
                    is_top = False
                    continue
                split_line = line.strip().lower().split(",")
                if material.strip().lower() == split_line[0]:
                    data_found = True
                    data_line = split_line
                    break
                  
        if not data_found:
            sys.exit("Invalid material prescribed: ", material)

        for i in range(0,len(title_line)):
            if title_line[i] == "e":
                mat_units = float(split_line[i])
                bar.E = float(mat_units)
            elif title_line[i] == "g":
                mat_units = float(split_line[i])
                bar.G = float(mat_units)
    

# Exchange data from being section to area information, etc
def LoadSectionData(bar, section, section_file = ""):
    if section_file == "":
        split_section = section.split(";")
        bar.A = float(split_section[0])
        if (len(split_section)>1):
            bar.It = float(split_section[1])
    else:
        data_found = False
        data_line = None
        title_line = None
        with open(section_file, 'r') as file:
            is_top = True
            for line in file:
                if is_top:
                    title_line = line.strip().lower().split(",")
                    is_top = False
                    continue
                
                split_line = line.strip().lower().split(",")
                if split_line[1]==section.strip().lower().split(":")[1]:
                    data_found = True
                    data_line = split_line
                    break
                  
        if not data_found:
            sys.exit("Invalid section prescribed")

        found_edi_notation = False
        for i in range(0,len(title_line)):
            if title_line[i] == "a":
                sec_units = float(split_line[i])
                bar.A = float(sec_units)
            elif title_line[i] == "ix":
                sec_units = float(split_line[i])
                bar.It = float(sec_units)
            elif title_line[i] == "iy":
                sec_units = float(split_line[i])
                bar.Iu = float(sec_units)
            elif title_line[i] == "w":
                sec_units = float(split_line[i])
                bar.self_weight = float(sec_units)
            elif title_line[i] == "EDI_Std_Nomenclature".lower():
                if found_edi_notation == True: # skip metric units
                    break
                else:
                    found_edi_notation = True # Assume imperial units
