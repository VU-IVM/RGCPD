#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 18 15:03:30 2020

@author: semvijverberg
"""

import os, inspect, sys
import numpy as np

user_dir = os.path.expanduser('~')
curr_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) # script directory
main_dir = '/'.join(curr_dir.split('/')[:-2])
RGCPD_func = os.path.join(main_dir, 'RGCPD')
cluster_func = os.path.join(main_dir, 'clustering/')
fc_dir = os.path.join(main_dir, 'forecasting')
if cluster_func not in sys.path:
    sys.path.append(main_dir)
    sys.path.append(RGCPD_func)
    sys.path.append(cluster_func)
    sys.path.append(fc_dir)

path_raw = user_dir + '/surfdrive/ERA5/input_raw'


from RGCPD import RGCPD
from RGCPD import BivariateMI
# from RGCPD import EOF



TVpath = '/Users/semvijverberg/surfdrive/output_RGCPD/circulation_US_HW/tf15_nc3_dendo_0ff31.nc'
path_out_main = os.path.join(main_dir, 'publications/paper2/output/east/')
cluster_label = 2
name_ds='ts'
start_end_TVdate = ('06-01', '08-31')
start_end_date = ('1-1', '12-31')
tfreq = 15
#%%
list_of_name_path = [(cluster_label, TVpath),
                      ('v200', os.path.join(path_raw, 'v200hpa_1979-2018_1_12_daily_2.5deg.nc')),
                       ('z500', os.path.join(path_raw, 'z500hpa_1979-2018_1_12_daily_2.5deg.nc')),
                       ('sst', os.path.join(path_raw, 'sst_1979-2018_1_12_daily_1.0deg.nc'))]



list_for_MI   = [BivariateMI(name='v200', func=BivariateMI.corr_map,
                              kwrgs_func={'alpha':.01, 'FDR_control':True},
                              distance_eps=600, min_area_in_degrees2=1,
                              calc_ts='pattern cov', selbox=(0,360,-10,90)),
                   BivariateMI(name='z500', func=BivariateMI.corr_map,
                                kwrgs_func={'alpha':.01, 'FDR_control':True},
                                distance_eps=600, min_area_in_degrees2=1,
                                calc_ts='pattern cov', selbox=(0,360,-10,90)),
                   BivariateMI(name='sst', func=BivariateMI.corr_map,
                                kwrgs_func={'alpha':.001, 'FDR_control':True},
                                distance_eps=600, min_area_in_degrees2=1,
                                calc_ts='pattern cov', selbox=(0,360,-10,90))]


rg = RGCPD(list_of_name_path=list_of_name_path,
            list_for_MI=list_for_MI,
            start_end_TVdate=start_end_TVdate,
            start_end_date=start_end_date,
            start_end_year=None,
            tfreq=tfreq, lags_i=np.array([0,1]),
            path_outmain=path_out_main,
            append_pathsub='_' + name_ds)


rg.pp_TV(name_ds=name_ds, detrend=False)

rg.pp_precursors()

rg.traintest('no_train_test_split')

rg.get_clust()
subtitles = np.array([['Clustered simultaneous high temp. events']])
plot_maps.plot_labels(rg.ds['xrclustered'], kwrgs_plot={'subtitles':subtitles})


import cartopy.crs as ccrs
rg.calc_corr_maps()
# rg.get_EOFs()


v200_green_bb = (170,359,23,73)
units = 'Corr. Coeff. [-]'
subtitles = np.array([[f'lag {l}: v-wind 200hpa vs eastern U.S. mx2t'] for l in rg.lags])
rg.plot_maps_corr(var='v200', row_dim='lag', col_dim='split',
                  aspect=2, size=5, hspace=-0.58, cbar_vert=.18, save=True,
                  subtitles=subtitles, units=units, zoomregion=(-180,360,0,80),
                  map_proj=ccrs.PlateCarree(central_longitude=220), n_yticks=6,
                  drawbox=['all', v200_green_bb],
                  clim=(-.6,.6))

z500_green_bb = (170,250,23,73)
subtitles = np.array([[f'lag {l}: z 500hpa vs eastern U.S. mx2t'] for l in rg.lags])
rg.plot_maps_corr(var='z500', row_dim='lag', col_dim='split',
                  aspect=2, size=5, hspace=-0.58, cbar_vert=.18, save=True,
                  subtitles=subtitles, units=units, zoomregion=(-180,360,0,80),
                  map_proj=ccrs.PlateCarree(central_longitude=220), n_yticks=6,
                  drawbox=['all', z500_green_bb],
                  clim=(-.6,.6))

SST_green_bb = (170,255,11,60)
subtitles = np.array([[f'lag {l}: SST vs eastern U.S. mx2t'] for l in rg.lags])
rg.plot_maps_corr(var='sst', row_dim='lag', col_dim='split',
                  aspect=2, hspace=-.57, size=5, cbar_vert=.175, save=True,
                  subtitles=subtitles, units=units, zoomregion=(-180,360,-10,70),
                  map_proj=ccrs.PlateCarree(central_longitude=220), n_yticks=6,
                  drawbox=['all', SST_green_bb],
                  clim=(-.6,.6))

#%% Determine Rossby wave within green rectangle, become target variable for feedback

rg.list_for_MI[0].selbox = v200_green_bb
rg.list_for_MI[1].selbox = z500_green_bb

rg.calc_corr_maps()#var='z500')
# subtitles = np.array([['E-U.S. Temp. correlation map Z 500hpa green box']])
# rg.plot_maps_corr(var='z500', cbar_vert=-.05, subtitles=subtitles, save=False)
rg.cluster_list_MI()#var='z500')
# rg.get_ts_prec(precur_aggr=None)
rg.get_ts_prec(precur_aggr=1)
rg.store_df()
#%% Determine Rossby wave within green rectangle, become target variable for HM

list_of_name_path = [(cluster_label, TVpath),
                     ('z500',os.path.join(path_raw, 'z500hpa_1979-2018_1_12_daily_2.5deg.nc')),
                     ('v200', os.path.join(path_raw, 'v200hpa_1979-2018_1_12_daily_2.5deg.nc')),]

list_for_MI   = [BivariateMI(name='z500', func=BivariateMI.corr_map,
                             kwrgs_func={'alpha':.01, 'FDR_control':True},
                             distance_eps=500, min_area_in_degrees2=1,
                             calc_ts='pattern cov', selbox=z500_green_bb),
                 BivariateMI(name='v200', func=BivariateMI.corr_map,
                             kwrgs_func={'alpha':.01, 'FDR_control':True},
                             distance_eps=500, min_area_in_degrees2=1,
                             calc_ts='pattern cov', selbox=v200_green_bb)]

rg = RGCPD(list_of_name_path=list_of_name_path,
           list_for_MI=list_for_MI,
           start_end_TVdate=start_end_TVdate,
           start_end_date=start_end_date,
           tfreq=tfreq, lags_i=np.array([0]),
           path_outmain=path_out_main,
           append_pathsub='_' + name_ds)


rg.pp_precursors(anomaly=True)
rg.pp_TV(name_ds=name_ds)

rg.traintest(method='no_train_test_split')

rg.calc_corr_maps()
subtitles = np.array([['E-U.S. Temp. correlation map Z 500hpa green box']])
rg.plot_maps_corr(var='z500', cbar_vert=-.05, subtitles=subtitles, save=False)
subtitles = np.array([['E-U.S. Temp. correlation map v200 green box']])
rg.plot_maps_corr(var='v200', cbar_vert=-.05, subtitles=subtitles, save=False)
rg.cluster_list_MI()
# rg.get_ts_prec(precur_aggr=None)
rg.get_ts_prec(precur_aggr=1)
# rg.store_df()


#%%
import class_RV
RV_ts = rg.fulltso.sel(time=rg.TV.aggr_to_daily_dates(rg.dates_TV))
threshold = class_RV.Ev_threshold(RV_ts, event_percentile=85)
RV_bin, np_dur = class_RV.Ev_timeseries(RV_ts, threshold=threshold, grouped=True)
plt.hist(np_dur[np_dur!=0])
