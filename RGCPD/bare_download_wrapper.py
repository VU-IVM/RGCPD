#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar  6 16:31:58 2019

@author: semvijverberg
"""

#%%
import os, inspect
import numpy as np
import pandas as pd
curr_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
script_dir = "/Users/semvijverberg/surfdrive/Scripts/RGCPD/RGCPD" # script directory
# To link modules in RGCPD folder to this script
os.chdir(script_dir)
# =============================================================================
# Data wil downloaded to path_raw
# =============================================================================
base_path = "/Users/semvijverberg/surfdrive/"
dataset   = 'era5' # choose 'era5' or 'ERAint' or era20c
exp_folder = 'RGCPD_jetlat'
path_raw = os.path.join(base_path,'Data_{}/' 
                        'input_raw'.format(dataset))
path_pp  = os.path.join(base_path, exp_folder, 'Data_{}/' 
                        'input_pp'.format(dataset))
if os.path.isdir(path_raw) == False : os.makedirs(path_raw)
if os.path.isdir(path_pp) == False: os.makedirs(path_pp)

# *****************************************************************************
# Step 1 Create dictionary and variable class (and optionally download ncdfs)
# *****************************************************************************
# The dictionary is used as a container with all information for the experiment
# The dic is saved after the post-processes step, so you can continue the experiment
# from this point onward with different configurations. It also stored as a log
# in the final output.

ex = dict(
     {'dataset'     :       dataset,
     'grid_res'     :       0.25,
     'startyear'    :       2001, # download startyear
     'endyear'      :       2018, # download endyear
     'months'       :       list(range(1,12+1)), #downoad months
     'input_freq'  :       'daily',
     'time'         :       pd.DatetimeIndex(start='00:00', end='23:00', 
                                freq=(pd.Timedelta(6, unit='h'))),
     'area'         :       [60, -130, 0, -60], # North, West, South, East. Default: global
     'base_path'    :       base_path,
     'path_raw'     :       path_raw,
     'path_pp'      :        path_pp}
     )

if ex['dataset'] == 'ERAint' or ex['dataset'] == 'era20c':
    import download_ERA_interim_API as ECMWF
elif ex['dataset'] == 'era5':
    import download_ERA5_API as ECMWF
    

# Option 1111111111111111111111111111111111111111111111111111111111111111111111
# Download ncdf fields (in ex['vars']) through cds?
# 11111111111111111111111111111111111111111111111111111111111111111111111111111
# only reanalysis fields

# Info to download ncdf from ECMWF, atm only analytical fields (no forecasts)
# You need the cds-api-client package for this option.

# See https://confluence.ecmwf.int/display/CKB/How+to+download+ERA5

ex['vars']     =   [
                    ['t2m', 'sst'],              # ['name_var1','name_var2', ...]
                    ['167.128', '34.128'],    # ECMWF param ids
                    ['sfc', 'sfc'],             # Levtypes
                    [['0'], ['0']],                  # Vertical levels
                    ]

for idx in range(len(ex['vars'][0]))[:]:
    # class for ECMWF downloads
    var_class = ECMWF.Var_ECMWF_download(ex, idx)
    ex[ex['vars'][0][idx]] = var_class
    ECMWF.retrieve_field(var_class)