#!/usr/bin/env python
# coding: utf-8

# In[1]:

import arcpy
import logging

arcpy.env.workspace = r"...gdb"
arcpy.env.overwriteOutput = True

buffer_fc = r"...shp" # input the polygon buffer feature class (fc) with the wetland acres data we will need to sum
polyline_fc = r"...shp" # input the polyline wetland intersect fc with the linear feet data we will need to sum
boundary_fc = r"...shp" # input the map series rectangles we are clipping the buffered wetland acres and linear feet with

logging.basicConfig(level=logging.INFO) # logging to see where errors occur in the code

def add_geometry_fields(fc, area_field="Calc_Area", length_field="Calc_Length"): #must recalculate geometry after clipping and before performing sum calculations
    logging.info(f"Checking and adding geometry fields for {fc}")
    fields = [f.name for f in arcpy.ListFields(fc)]
    
    if area_field not in fields:
        arcpy.AddField_management(fc, area_field, "DOUBLE")
    if length_field not in fields:
        arcpy.AddField_management(fc, length_field, "DOUBLE")

def clip_and_summarize(i):
    try:
        arcpy.MakeFeatureLayer_management(boundary_fc, "boundary_layer")
        arcpy.SelectLayerByAttribute_management("boundary_layer", "NEW_SELECTION", f"SeqId = {i}")
        selected_count = int(arcpy.GetCount_management("boundary_layer")[0])
        
        if selected_count == 0:
            logging.warning(f"No features selected for SeqId = {i}. Skipping.")
            return None, None

        # Clip buffer
        clip_buffer_fc = f"clip_buffer_fc_{i}"
        arcpy.Clip_analysis(buffer_fc, "boundary_layer", clip_buffer_fc)
        add_geometry_fields(clip_buffer_fc)
        arcpy.CalculateGeometryAttributes_management(clip_buffer_fc, [["Calc_Area", "AREA_GEODESIC"]])
        arcpy.CalculateField_management(clip_buffer_fc, "Calc_Area", "!Calc_Area! / 4046.85642", "PYTHON3") # acres conversion

        # Clip polyline
        clip_polyline_fc = f"clip_polyline_fc_{i}"
        arcpy.Clip_analysis(polyline_fc, "boundary_layer", clip_polyline_fc)
        add_geometry_fields(clip_polyline_fc, length_field="Calc_Length")
        arcpy.CalculateGeometryAttributes_management(clip_polyline_fc, [["Calc_Length", "LENGTH_GEODESIC"]])
        arcpy.CalculateField_management(clip_polyline_fc, "Calc_Length", "!Calc_Length! * 3.28084", "PYTHON3") # linear feet conversion 
        
        # Spatial join to retain SeqId
        joined_clip_buffer_fc = f"joined_clip_buffer_fc_{i}"
        joined_clip_polyline_fc = f"joined_clip_polyline_fc_{i}"
        arcpy.analysis.SpatialJoin(clip_buffer_fc, boundary_fc, joined_clip_buffer_fc, join_type="KEEP_COMMON")
        arcpy.analysis.SpatialJoin(clip_polyline_fc, boundary_fc, joined_clip_polyline_fc, join_type="KEEP_COMMON")
        
        logging.info(f"Clipping and spatial join complete for SeqId {i}")
        return joined_clip_buffer_fc, joined_clip_polyline_fc
    except Exception as e:
        logging.error(f"Error during clipping for SeqId {i}: {e}")
        return None, None

# Merge and summarize

def create_master_tables():
    buffer_joined_tables = []
    polyline_joined_tables = []

    for i in range(1, 21):
        buffer_fc, polyline_fc = clip_and_summarize(i)
        if buffer_fc:
            buffer_joined_tables.append(buffer_fc)
        if polyline_fc:
            polyline_joined_tables.append(polyline_fc)

    master_buffer_table = "Master_Joined_Buffer"
    master_polyline_table = "Master_Joined_Polyline"

    if arcpy.Exists(master_buffer_table):
        arcpy.Delete_management(master_buffer_table)
    if arcpy.Exists(master_polyline_table):
        arcpy.Delete_management(master_polyline_table)

    if buffer_joined_tables:
        arcpy.management.Merge(buffer_joined_tables, master_buffer_table)
        summarize(master_buffer_table, "Calc_Area", "Cowardin_Aggregate", "Buffer_Summary_Master")
    
    if polyline_joined_tables:
        arcpy.management.Merge(polyline_joined_tables, master_polyline_table)
        summarize(master_polyline_table, "Calc_Length", "Cowardin_Aggregate", "Polyline_Summary_Master")

    logging.info("Master tables created and summarized.")

# Summarize by Cowardin class and SeqId

def summarize(input_fc, sum_field, case_field, output_table):
    if arcpy.Exists(output_table):
        arcpy.Delete_management(output_table)

    summary_fields = [[sum_field, "SUM"]]
    case_fields = [case_field, "SeqId"]
    
    arcpy.Statistics_analysis(input_fc, output_table, summary_fields, case_fields)
    logging.info(f"Summary table created: {output_table}")

create_master_tables()


# In[ ]:

