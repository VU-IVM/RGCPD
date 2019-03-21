#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb  7 15:42:46 2019

@author: semvijverberg
"""
import os
import numpy as np


def Variable(self, ex):
    self.startyear = ex['startyear']
    self.endyear = ex['endyear']
    self.months = ex['months']
    self.startmonth = min(ex['months'])
    self.endmonth   = max(ex['months'])
    self.grid = ['{}'.format(ex['grid_res']),'{}'.format(ex['grid_res'])]
    self.dataset = ex['dataset']
    self.path_raw = ex['path_raw']
    self.path_pp = ex['path_pp']
    self.base_path = ex['base_path']
    return self

class Var_ECMWF_download():
    """Levtypes: \n surface  :   sfc \n model level  :   ml (1 to 137) \n pressure levels (1000, 850.. etc)
    :   pl \n isentropic level    :   pt
    \n
    Monthly Streams:
    Monthly mean of daily mean  :   moda
    Monthly mean of analysis timesteps (synoptic monthly means)  :   mnth
    Daily Streams:
    Operational (for surface)   :   oper
    """
    
    
    def __init__(self, ex, idx):

#        from datetime import datetime, timedelta
#        import pandas as pd
#        import calendar
#        import os
        vclass = Variable(self, ex)
        # shared information of ECMWF downloaded variables
        # variables specific information
        if ex['vars'][2][idx] == 'sfc':
            vclass.dataset = '{}'.format('reanalysis-era5-single-levels')
        vclass.name = ex['vars'][0][idx]
        vclass.var_cf_code = ex['vars'][1][idx]
        vclass.levtype = ex['vars'][2][idx]
        vclass.lvllist = ex['vars'][3][idx]
        if 'area' in ex.keys():
            vclass.area    = ex['area']
        else:
            vclass.area    = 'global'
        if ex['input_freq'] == 'daily':
            vclass.stream = 'oper'
            vclass.input_freq = 'daily'
        if ex['input_freq'] == 'monthly':
            vclass.stream = 'moda'
            vclass.input_freq = 'monthly'
            
        vclass.years    = [str(yr) for yr in np.arange(ex['startyear'], 
                                               ex['endyear']+1E-9, dtype=int)]
        vclass.months   = [str(yr) for yr in ex['months']] 
        vclass.days     = [str(yr) for yr in np.arange(1, 31+1E-9, dtype=int)] 
        

        vclass.time = list(ex['time'].strftime('%H:%M'))


        vclass.filename = '{}_{}-{}_{}_{}_{}_{}deg.nc'.format(vclass.name, 
                           vclass.startyear, vclass.endyear, vclass.startmonth, 
                           vclass.endmonth, ex['input_freq'], ex['grid_res']).replace(' ', '_')
        vclass.format = '{}'.format('netcdf')
        print(('\n\t**\n\t{} {}-{} {} data on {} grid\n\t**\n'.format(vclass.name, 
               vclass.startyear, vclass.endyear, ex['input_freq'], vclass.grid)))
        
        
            
def retrieve_field(cls):
    import os
    
    file_path = os.path.join(cls.path_raw, cls.filename)
    if cls.stream == 'moda':
        file_path_raw = file_path
    else: 
        file_path_raw = file_path.replace('daily','oper')
    
    if os.path.isfile(path=file_path) == True:
        print("You have already download the variable")
        print(("to path: {} \n ".format(file_path)))
        pass
    else:
        # create temporary folder
        cls.tmp_folder = os.path.join(cls.path_raw, 
                  '{}_{}_{}_tmp'.format(cls.name, cls.stream, cls.grid[0]))
        if os.path.isdir(cls.tmp_folder) == False : os.makedirs(cls.tmp_folder)
        print(("You WILL download variable {} \n stream is set to {} \n".format \
            (cls.name, cls.stream)))
        print(("to path: \n \n {} \n \n".format(file_path_raw)))
        
        # =============================================================================
        #         daily data
        # =============================================================================
        if cls.stream == 'oper':
            
            for year in cls.years:
                # specifies the output file name
                target = os.path.join(cls.tmp_folder, 
                          '{}_{}.nc'.format(cls.name, year))   
                if os.path.isfile(target) == False:
                    print('Output file: ', target)
                    retrieval_yr(cls, year, target)
    
            print("convert operational 6hrly data to daily means")
            cat  = 'cdo cat {}*.nc {}'.format(cls.tmp_folder, file_path_raw)
            daymean = 'cdo daymean {} {}'.format(file_path_raw, file_path)
            args = [cat, daymean]
            kornshell_with_input(args, cls)


        # =============================================================================
        # monthly mean of daily means            
        # =============================================================================
        if cls.stream == 'moda':
            years = [int(yr) for yr in cls.years]
            decades = list(set([divmod(i, 10)[0] for i in years]))
            decades = [x * 10 for x in decades]
            decades.sort()
            print('Decades:', decades)
          
        # loop through decades and create a month list
            for d in decades:
                requestDates=''
                for y in years:
                    if ((divmod(y,10)[0])*10) == d:
                        for m in cls.months:
                            requestDates = requestDates+str(y)+m.zfill(2)+'01/'
                requestDates = requestDates[:-1]
                print('Requesting dates: ', requestDates)
                target = os.path.join(cls.tmp_folder, '{}_{}.nc'.format(cls.name,
                              year))  
                if os.path.isfile(target) == False:
                    print('Output file: ', target)
                    retrieval_moda(cls, requestDates, d, target)
        
    return

def retrieval_yr(cls, year, target):
    import cdsapi
    server = cdsapi.Client()

    

    # !/usr/bin/python
    if cls.levtype == 'sfc':
        server.retrieve("reanalysis-era5-single-levels",
            {
            "product_type":  "reanalysis",
            "class"     :   "ei",
            "expver"    :   "1",
            "grid"      :   cls.grid,
            "year"      :   year,
            "month"     :   cls.months,
            "day"       :   cls.days,
            'area'      :   cls.area,
#                "levtype"   :   cls.levtype,
            # "levelist"  :   cls.lvllist,
            "param"     :   cls.var_cf_code,
            "time"      :  cls.time,
            "format"    :   "netcdf",
            }, 
            target)
    elif cls.levtype == 'pl':
        server.retrieve("reanalysis-era5-pressure-levels",
            {
            "product_type":  "reanalysis",
            "class"     :   "ei",
            "expver"    :   "1",
            "grid"      :   cls.grid,
            "year"      :   year,
            "month"     :   cls.months,
            "day"       :   cls.days,
            'area'      :   cls.area,
            "levelist"  :   cls.lvllist,
            "param"     :   cls.var_cf_code,
             "time"      :  cls.time,
            "format"    :   "netcdf",
            }, 
            target)
    return


def retrieval_moda(cls, requestDates, decade, target):
    import cdsapi
    server = cdsapi.Client()

    if cls.levtype == 'sfc':
        server.retrieve('reanalysis-era5-complete', {    # do not change this!
        'class'         :   'ea',
        'expver'        :   '1',
        'stream'        :   'moda',
        'type'          :   'an',
        'param'         :   cls.var_cf_code,
        'levtype'       :   cls.levtype,
        'date'          :   requestDates,
        'decade'        :   decade,
        }, target)
    elif cls.levtype == 'pl': 
        server.retrieve('reanalysis-era5-complete', {    # do not change this!
        'class'         :   'ea',
        'expver'        :   '1',
        'stream'        :   'moda',
        'type'          :   'an',
        'param'         :   cls.var_cf_code,
        'levtype'       :   cls.levtype,
        'levelist'      :   cls.lvllist,
        'date'          :   requestDates,
        'decade'        :   decade,
        }, target)


def kornshell_with_input(args, cls):
    '''some kornshell with input '''
    import subprocess
    cwd = os.getcwd()
    # Writing the bash script:
    new_bash_script = os.path.join(cwd,'bash_scripts', "bash_script.sh")
    
    bash_and_args = [new_bash_script]
    [bash_and_args.append(arg) for arg in args]
    with open(new_bash_script, "w") as file:
        file.write("#!/bin/sh\n")
        file.write("echo bash script output\n")
        for cmd in range(len(args)):

            print(args[cmd].replace(cls.base_path, 'base_path/')[:300])
            file.write("${}\n".format(cmd+1)) 
    p = subprocess.Popen(bash_and_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, 
                         stderr=subprocess.STDOUT)
                         
    out = p.communicate()
    print(out[0].decode())
    return


#ex = dict(
#     {'dataset'     :       'ERA-5',
#     'grid_res'     :       0.5,
#     'startyear'    :       1979, # download startyear
#     'endyear'      :       2018, # download endyear
#     'firstmonth'   :       1,
#     'lastmonth'    :       12,
#     'time'         :       pd.DatetimeIndex(start='00:00', end='23:00', 
#                                freq=(pd.Timedelta(6, unit='h'))),
#     'format'       :       'netcdf',
#     'base_path'    :       base_path,
#     'path_raw'     :       path_raw,
#     'path_pp'     :        path_pp}
#     )
#
#ex['vars'] = [['2m_temperature'],['34.128'],['sfc'],['0']]
#
#vclass = Var_ECMWF_download(ex, idx=0)
#
#
#dict_retrieval =  ('\'{}\',\n\t{{\n'.format(vclass.dataset)+
#                     '\t\'variable\'         :   \'{}\',\n'.format(vclass.name)+
#                     '\t\'product_type\'     :   \'reanalysis\',\n'
#                     '\t\'year\'         :     {},\n'.format(vclass.years)+
#                     '\t\'month\'        :     {},\n'.format(vclass.months)+
#                     '\t\'day\'          :     {},\n'.format(vclass.days)+
#                     '\t\'grid\'         :     {},\n'.format(vclass.grid)+
#                     '\t\'time\'         :     {},\n'.format(vclass.time)+
#                     '\t\'format\'       :     \'{}\',\n'.format(vclass.format)+
#                     '\t}'
#                     )
#print(dict_retrieval)