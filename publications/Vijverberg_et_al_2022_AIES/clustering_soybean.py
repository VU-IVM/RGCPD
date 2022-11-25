#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  5 09:35:06 2020

@author: semvijverberg
"""

import os, inspect, sys
sys.path.remove('/Users/semvijverberg/surfdrive/Scripts/jannes_code/RGCPD')
import numpy as np
import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt
user_dir = os.path.expanduser('~')
curr_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) # script directory
main_dir = '/'.join(curr_dir.split('/')[:-2])
if main_dir not in sys.path:
    sys.path.append(curr_dir)
    sys.path.append(main_dir)



if sys.platform == 'linux':
    import matplotlib as mpl
    mpl.use('Agg')

# path with USDA .nc gridded data. Provided by Raed Hamed.
root_data = user_dir+'/surfdrive/Scripts/RGCPD/publications/Vijverberg_et_al_2022_AIES/data/'
# path to store cluster output figures and netcdfs
path_outmain = user_dir+'/surfdrive/Scripts/RGCPD/publications/Vijverberg_et_al_2022_AIES/clustering'

import utils_paper3
from RGCPD import plot_maps, core_pp, functions_pp
from RGCPD.clustering import clustering_spatial as cl
from RGCPD.clustering import make_country_mask
import cartopy.feature as cfeature

#%% Soy bean GDHY
apply_mask_nonans = True
detrend_via_spatial_mean = False
missing_years = 1
percen_years = missing_years / 70
percen_years = 15


raw_filename = os.path.join(root_data, 'masked_rf_gs_county_grids.nc')
selbox = [253,290,28,52] ; years = list(range(1975, 2020))

ds_raw = core_pp.import_ds_lazy(raw_filename, selbox=selbox)['variable'].rename({'z':'time'})
ds_raw.name = 'Soy_Yield'
ds_raw['time'] = pd.to_datetime([f'{y+1949}-01-01' for y in ds_raw.time.values])
ds_raw = ds_raw.sel(time=core_pp.get_oneyr(ds_raw, *years))



ano = (ds_raw - ds_raw.mean(dim='time')) / ds_raw.std(dim='time')

plt.figure()
ds_avail = (70 - np.isnan(ano).sum(axis=0))
ds_avail = ds_avail.where(ds_avail.values >= 30)
ds_avail.plot(vmin=30) # number of years with data available
ds_avail.min()

ano = core_pp.detrend_xarray_ds_2D(ano, detrend={'method':'linear'}, anomaly=False,
                             kwrgs_NaN_handling={'missing_data_ts_to_nan':percen_years,
                                                 'extra_NaN_limit':0.15, # 15%
                                                 'final_NaN_to_clim':True})


#%%
# if apply_mask_nonans:
#     allways_data_mask = np.isnan(ano).sum(dim='time') <= missing_years
#     ano = ano.where(allways_data_mask)
#     if missing_years != 0:
#         ano = ano.interpolate_na(dim='time', limit=2) # max 2 consecutive NaNs
#         allways_data_mask = np.isnan(ano).sum(dim='time') <= 0
#         ano = ano.where(allways_data_mask)
# # plot_maps.plot_corr_maps(ano, row_dim='time', cbar_vert=.09)
# if detrend_via_spatial_mean :
#     detrend_spat_mean = ano.mean(dim=('latitude', 'longitude'))
#     trend = detrend_spat_mean - core_pp.detrend(detrend_spat_mean, method='loess')
#     ano = ano - trend
# else:
#     ano = core_pp.detrend(ano, method='loess')

var_filename = raw_filename[:-3] + '_pp.nc'
ano.to_netcdf(var_filename)

#%%


da = core_pp.import_ds_lazy(var_filename)
xr_States, States = make_country_mask.create_mask(da, level='US_States', path=path_outmain)
xr_States = xr_States.where(xr_States.values != -1)

#%% Get colormap

cmp = plot_maps.get_continuous_cmap(["ffbe0b","fb5607","ff006e","8338ec","3a86ff"],
                          float_list=list(np.linspace(0,1,5)))

# =============================================================================
# Clustering Ward Hierarchical Agglomerative Clustering
# =============================================================================
from time import time
t0 = time()
xrclusteredall, results = cl.sklearn_clustering(var_filename, mask=~np.isnan(ano).all(axis=0),
                                               kwrgs_load={'tfreq':None,
                                                           'seldates':None,
                                                           'selbox':None},
                                               clustermethodkey='AgglomerativeClustering',
                                               kwrgs_clust={'n_clusters':[2,4,6,8],
                                                            'affinity':'euclidean',
                                                            'linkage':'ward'})

title = 'Hierarchical Aggl. Clustering'
# r = np.meshgrid(xrclusteredall.n_clusters.astype(str).values)
r = xrclusteredall.n_clusters.astype(str).values
# subtitles = [f'n-clusters={r.flatten()[i]}, ' + f'random state={c.flatten()[i]}' for i in range(c.size)]
subtitles = [f'n-clusters={r.flatten()[i]}, linkage=ward, metric=euclidean' for i in range(r.size)]
fig = plot_maps.plot_labels(xrclusteredall,
                            kwrgs_plot={'wspace':.05, 'hspace':.17, 'cbar_vert':.045,
                                        'row_dim':'n_clusters', 'col_dim':'linkage',
                                        'zoomregion':selbox, 'cmap':cmp,
                                        'x_ticks':np.array([260,270,280]),
                                        'y_ticks':np.array([32, 37, 42, 47]),
                                        'title':title,
                                        'title_fontdict':{'y':.93,
                                                          'fontsize': 18,
                                                          'fontweight':'bold'}})
for i, ax in enumerate(fig.axes.flatten()):
    np.isnan(xr_States).plot.contour(ax=ax,
                                     transform=plot_maps.ccrs.PlateCarree(),
                                     linestyles=['solid'],
                                     colors=['black'],
                                     linewidths=2,
                                     levels=[0,1],
                                     add_colorbar=False)
    ax.add_feature(cfeature.NaturalEarthFeature(
        'cultural', 'admin_1_states_provinces_lines', '50m',
        edgecolor='grey', lw=1, facecolor='none'))
    ax.add_feature(cfeature.OCEAN)
    ax.add_feature(cfeature.LAKES)
    ax.add_feature(cfeature.COASTLINE)
    ax.set_ylabel(None) ; ax.set_xlabel(None)
    ax.set_title(subtitles[i], fontsize=12)


#%%
f_name = 'clustering_Hierchical_ward_{}'.format(xrclusteredall.attrs['hash'])
path_fig = os.path.join(path_outmain, f_name)
plt.savefig(path_fig + '.pdf', bbox_inches='tight') # dpi auto 600

plt.savefig(path_fig + '.jpeg', bbox_inches='tight') # dpi auto 600
print(f'{round(time()-t0, 2)}')

#%%
# =============================================================================
# Clustering correlation Hierarchical Agglomerative Clustering
# =============================================================================
from time import time
t0 = time()
xrclusteredall, results = cl.sklearn_clustering(var_filename, mask=~np.isnan(ano).all(axis=0),
                                               kwrgs_load={'tfreq':None,
                                                           'seldates':None,
                                                           'selbox':None},
                                               clustermethodkey='AgglomerativeClustering',
                                               kwrgs_clust={'n_clusters':[2,4,6,8],
                                                            'affinity':'correlation',
                                                            'linkage':'average'})

fig = plot_maps.plot_labels(xrclusteredall,
                            kwrgs_plot={'wspace':.05, 'hspace':.15, 'cbar_vert':.045,
                                        'row_dim':'n_clusters',
                                        'zoomregion':selbox, 'cmap':cmp,
                                        'x_ticks':np.array([260,270,280]),
                                        'y_ticks':np.array([32, 37, 42, 47]),
                                        'title':title,
                                        'title_fontdict':{'y':.93,
                                                          'fontsize': 18,
                                                          'fontweight':'bold'}})

title = 'Hierarchical Aggl. Clustering'
# r = np.meshgrid(xrclusteredall.n_clusters.astype(str).values)
r = xrclusteredall.n_clusters.astype(str).values
# subtitles = [f'n-clusters={r.flatten()[i]}, ' + f'random state={c.flatten()[i]}' for i in range(c.size)]
subtitles = [f'n-clusters={r.flatten()[i]}, linkage=average, metric=correlation' for i in range(r.size)]

for i, ax in enumerate(fig.axes.flatten()):
    np.isnan(xr_States).plot.contour(ax=ax,
                                     transform=plot_maps.ccrs.PlateCarree(),
                                     linestyles=['solid'],
                                     colors=['black'],
                                     linewidths=2,
                                     levels=[0,1],
                                     add_colorbar=False)
    ax.add_feature(cfeature.NaturalEarthFeature(
        'cultural', 'admin_1_states_provinces_lines', '50m',
        edgecolor='grey', lw=1, facecolor='none'))
    ax.add_feature(cfeature.OCEAN)
    ax.add_feature(cfeature.LAKES)
    ax.add_feature(cfeature.COASTLINE)
    ax.set_ylabel(None) ; ax.set_xlabel(None)
    ax.set_title(subtitles[i], fontsize=12)

#%%
f_name = 'clustering_Hierchical_correlation_{}'.format(xrclusteredall.attrs['hash'])
path_fig = os.path.join(path_outmain, f_name)
plt.savefig(path_fig + '.pdf', bbox_inches='tight') # dpi auto 600

plt.savefig(path_fig + '.jpeg', bbox_inches='tight') # dpi auto 600
print(f'{round(time()-t0, 2)}')

#%%
# =============================================================================
# Clustering K-means Euclidian
# =============================================================================
from time import time
t0 = time()
xrclusteredall, results = cl.sklearn_clustering(var_filename, mask=np.mean(~np.isnan(ano), axis=0) == 1,
                                               kwrgs_load={'tfreq':None,
                                                           'seldates':None,
                                                           'selbox':None},
                                               clustermethodkey='KMeans',
                                               kwrgs_clust={'n_clusters':[2,4,6,8],
                                                            'random_state':0})
                                                            # 'linkage':'average'})

title = 'K-means'
# r = np.meshgrid(xrclusteredall.n_clusters.astype(str).values)
r = xrclusteredall.n_clusters.astype(str).values
# subtitles = [f'n-clusters={r.flatten()[i]}, ' + f'random state={c.flatten()[i]}' for i in range(c.size)]
subtitles = [f'n-clusters={r.flatten()[i]}, metric=euclidean' for i in range(r.size)]


fig = plot_maps.plot_labels(xrclusteredall,
                            kwrgs_plot={'wspace':.05, 'hspace':.16, 'cbar_vert':.045,
                                        'row_dim':'n_clusters', 'col_dim':'random_state',
                                        'zoomregion':selbox, 'cmap':cmp,
                                        'x_ticks':np.array([260,270,280]),
                                        'y_ticks':np.array([32, 37, 42, 47]),
                                        'title':title,
                                        'title_fontdict':{'y':.93,
                                                          'fontsize': 18,
                                                          'fontweight':'bold'}})
for i, ax in enumerate(fig.axes.flatten()):
    np.isnan(xr_States).plot.contour(ax=ax,
                                     transform=plot_maps.ccrs.PlateCarree(),
                                     linestyles=['solid'],
                                     colors=['black'],
                                     linewidths=2,
                                     levels=[0,1],
                                     add_colorbar=False)
    ax.add_feature(cfeature.NaturalEarthFeature(
        'cultural', 'admin_1_states_provinces_lines', '50m',
        edgecolor='grey', lw=1, facecolor='none'))
    ax.add_feature(cfeature.OCEAN)
    ax.add_feature(cfeature.LAKES)
    ax.add_feature(cfeature.COASTLINE)
    ax.set_ylabel(None) ; ax.set_xlabel(None)
    ax.set_title(subtitles[i], fontsize=12)

#%%
f_name = 'clustering_KMeans_{}'.format(xrclusteredall.attrs['hash'])
path_fig = os.path.join(path_outmain, f_name)
plt.savefig(path_fig + '.pdf', bbox_inches='tight') # dpi auto 600

f_name = 'clustering_KMeans_{}'.format(xrclusteredall.attrs['hash'])
path_fig = os.path.join(path_outmain, f_name)
plt.savefig(path_fig + '.jpeg', bbox_inches='tight') # dpi auto 600



print(f'{round(time()-t0, 2)}')
print(f'{round(time()-t0, 2)}')

#%%
# =============================================================================
# Clustering co-occurence of anomalies Hierarchical Agglomerative Clustering
# =============================================================================
from time import time

quantiles = [50,55,60,65]
n_clusters = [2,3,4,5,6,7,8]

t0 = time()
xrclusteredall, results = cl.dendogram_clustering(var_filename, mask=np.mean(~np.isnan(ano), axis=0) == 1,
                                               kwrgs_load={'tfreq':None,
                                                           'seldates':None,
                                                           'selbox':None},
                                               kwrgs_clust={'q':quantiles,
                                                            'n_clusters':n_clusters,
                                                            'affinity':'jaccard',
                                                            'linkage':'average'},
                                               n_cpu=3)

plot_maps.plot_labels(xrclusteredall,  kwrgs_plot={'wspace':.05, 'hspace':.15, 'cbar_vert':.05,
                      'row_dim':'n_clusters', 'col_dim':'q'})

f_name = 'clustering_Hierchical_dendogram_{}'.format(xrclusteredall.attrs['hash']) + '.pdf'
path_fig = os.path.join(path_outmain, f_name)
plt.savefig(path_fig,
            bbox_inches='tight') # dpi auto 600
print(f'{round(time()-t0, 2)}')


#%% New idea 11-10-21, extrapolate mask to get more data into the cluster spatial mean timeseries (not used)
# didn't really help

xrclusteredall, results = cl.sklearn_clustering(var_filename, mask=~np.isnan(ano).all(axis=0),
                                               kwrgs_load={'tfreq':None,
                                                           'seldates':None,
                                                           'selbox':None},
                                               clustermethodkey='AgglomerativeClustering',
                                               kwrgs_clust={'n_clusters':[2,4,6,8],
                                                            'affinity':'euclidean',
                                                            'linkage':'ward'})

cmp = plot_maps.get_continuous_cmap(["fb5607", "3a86ff"],
                          float_list=list(np.linspace(0,1,2)))
subtitles = ['linkage=ward, metric=euclidean', 'Interpolated']
title = 'Hierarchical Aggl. Clustering'
linkage = 'ward' ; c =2
attrs = xrclusteredall.attrs



kwrgs_NaN_handling={'missing_data_ts_to_nan':False,
                    'extra_NaN_limit':False,
                    'inter_method':False,
                    'final_NaN_to_clim':False}
years = list(range(1950, 2020))
ds_raw = core_pp.import_ds_lazy(raw_filename, var='variable', selbox=selbox,
                                kwrgs_NaN_handling=kwrgs_NaN_handling).rename({'z':'time'})
ds_raw.name = 'Soy_Yield'
ds_raw['time'] = pd.to_datetime([f'{y+1949}-01-01' for y in ds_raw.time.values])
ds_raw = ds_raw.sel(time=core_pp.get_oneyr(ds_raw, *years))

ds_avail = (70 - np.isnan(ds_raw).sum(axis=0))
ds_avail = ds_avail.where(ds_avail.values >=30)


xrclusteredint = xrclusteredall.sel(n_clusters=c)
latint = xrclusteredint.interpolate_na(dim='latitude', limit=5)
xrclustfinalint = latint.interpolate_na(dim='longitude', limit=10)
# title = 'Clusters Interpolated'
xrclustfinalint = xrclustfinalint.where(~np.isnan(ds_avail))
# round to integer label
xrclustfinalint = np.round(xrclustfinalint+0.49)
xrclustfinalint.attrs = attrs

to_plot = xr.concat([xrclusteredall.sel(n_clusters=c), xrclustfinalint], dim='lag')
to_plot['lag'] = ('lag', [0,1])


fig = plot_maps.plot_labels(to_plot.drop('n_clusters'),
                            kwrgs_plot={'wspace':.05, 'hspace':.16, 'cbar_vert':-.1,
                                        'col_dim':'lag',
                                        'zoomregion':selbox, 'cmap':cmp,
                                        'x_ticks':np.array([260,270,280]),
                                        'y_ticks':np.array([32, 37, 42, 47]),
                                        'title':title,
                                        'title_fontdict':{'y':1.02,
                                                          'fontsize': 18,
                                                          'fontweight':'bold'}})
for i, ax in enumerate(fig.axes.flatten()):
    np.isnan(xr_States).plot.contour(ax=ax,
                                     transform=plot_maps.ccrs.PlateCarree(),
                                     linestyles=['solid'],
                                     colors=['black'],
                                     linewidths=2,
                                     levels=[0,1],
                                     add_colorbar=False)
    ax.add_feature(cfeature.NaturalEarthFeature(
        'cultural', 'admin_1_states_provinces_lines', '50m',
        edgecolor='grey', lw=1, facecolor='none'))
    ax.add_feature(cfeature.OCEAN)
    ax.add_feature(cfeature.LAKES)
    ax.add_feature(cfeature.COASTLINE)
    ax.set_ylabel(None) ; ax.set_xlabel(None)
    ax.set_title(subtitles[i], fontsize=14)

f_name = 'clustering_interp_{}'.format(xrclusteredall.attrs['hash'])
path_fig = os.path.join(path_outmain, f_name)
plt.savefig(path_fig + '.pdf', bbox_inches='tight') # dpi auto 600

f_name = 'clustering_interp_{}'.format(xrclusteredall.attrs['hash'])
path_fig = os.path.join(path_outmain, f_name)
plt.savefig(path_fig + '.jpeg', bbox_inches='tight') # dpi auto 600

#%% Get timeseries interpolated method


ds_std = (ds_raw - ds_raw.mean(dim='time')) / ds_raw.std(dim='time')
ds = cl.spatial_mean_clusters(ds_std,
                              xrclustfinalint)
df = ds.ts.to_dataframe().pivot_table(index='time', columns='cluster')['ts']

f_name = 'linkage_{}_nc{}'.format(linkage, int(c))
filepath = os.path.join(path_outmain, f_name)
cl.store_netcdf(ds, filepath=filepath, append_hash='dendo_interp_'+xrclustfinalint.attrs['hash'])

#%% get timeseries with per gridcell detrending (Used)
# using Aggl Clustering with linkage ward, affinity euclidean

xrclusteredall, results = cl.sklearn_clustering(var_filename, mask=~np.isnan(ano).all(axis=0),
                                               kwrgs_load={'tfreq':None,
                                                           'seldates':None,
                                                           'selbox':None},
                                               clustermethodkey='AgglomerativeClustering',
                                               kwrgs_clust={'n_clusters':[2,4,6,8],
                                                            'affinity':'euclidean',
                                                            'linkage':'ward'})

kwrgs_NaN_handling={'missing_data_ts_to_nan':False,
                    'extra_NaN_limit':False,
                    'inter_method':False,
                    'final_NaN_to_clim':False}
years = list(range(1950, 2020))
ds_raw = core_pp.import_ds_lazy(raw_filename, var='variable', selbox=selbox,
                                kwrgs_NaN_handling=kwrgs_NaN_handling).rename({'z':'time'})
ds_raw.name = 'Soy_Yield'
ds_raw['time'] = pd.to_datetime([f'{y+1949}-01-01' for y in ds_raw.time.values])
ds_raw = ds_raw.sel(time=core_pp.get_oneyr(ds_raw, *years))

ds_detr = utils_paper3.detrend_oos_3d(ds_raw, min_length=30)

ds_std = (ds_detr - ds_detr.mean(dim='time')) / ds_detr.std(dim='time')
linkage = 'ward' ; c =2

xrclustered = xrclusteredall.sel(n_clusters=c)


ds = cl.spatial_mean_clusters(ds_std,
                              xrclustered)
dfnew = ds.ts.to_dataframe().pivot_table(index='time', columns='cluster')['ts']

f_name = 'linkage_{}_nc{}'.format(linkage, int(c))
filepath = os.path.join(path_outmain, f_name)
cl.store_netcdf(ds, filepath=filepath, append_hash='dendo_'+xrclustered.attrs['hash'])
path_stored_cluster = os.path.join(filepath +'_'+ 'dendo_'+xrclustered.attrs['hash'])

#%% get timeseries (no linear detrending before standardizing) - not neat

kwrgs_NaN_handling={'missing_data_ts_to_nan':40,
                    'extra_NaN_limit':False,
                    'inter_method':False,
                    'final_NaN_to_clim':False}
years = list(range(1950, 2020))
ds_raw = core_pp.import_ds_lazy(raw_filename, var='variable', selbox=selbox,
                                kwrgs_NaN_handling=kwrgs_NaN_handling).rename({'z':'time'})
ds_raw.name = 'Soy_Yield'
ds_raw['time'] = pd.to_datetime([f'{y+1949}-01-01' for y in ds_raw.time.values])
ds_raw = ds_raw.sel(time=core_pp.get_oneyr(ds_raw, *years))

ds_avail = (70 - np.isnan(ds_raw).sum(axis=0))
ds_avail = ds_avail.where(ds_avail.values !=0)
ds_avail.plot(vmin=30)
ds_avail.min()


ds_std = (ds_raw - ds_raw.mean(dim='time')) / ds_raw.std(dim='time')


linkage = 'ward' ; c =2
xrclustered = xrclusteredall.sel(n_clusters=c)



ds = cl.spatial_mean_clusters(ds_std,
                              xrclustered)
df = ds.ts.to_dataframe().pivot_table(index='time', columns='cluster')['ts']

f_name = 'linkage_{}_nc{}'.format(linkage, int(c))
filepath = os.path.join(path_outmain, f_name)
cl.store_netcdf(ds, filepath=filepath, append_hash='dendo_'+xrclustered.attrs['hash'])

#%% consequence of linear detrending prior to standardizing

f, ax = plt.subplots(1) ; _df = core_pp.detrend_wrapper(df[[1]],plot=False) ;
ax.plot(_df) ; ax.plot(dfnew[[1]], color='red')

#%% Figure 1 paper

cmp = plot_maps.get_continuous_cmap(["fb5607", "ffbe0b"],
                          float_list=list(np.linspace(0,1,2)))

title = 'Hierarchical Aggl. Clustering'
xrclustfinal = xrclusteredall[0]
fig = plot_maps.plot_labels(xrclustfinal,
                            kwrgs_plot={'wspace':.05, 'hspace':.15, 'cbar_vert':-.1,
                                        'row_dim':'n_clusters',
                                        'zoomregion':selbox, 'cmap':cmp,
                                        'x_ticks':np.array([260,270,280]),
                                        'title':title,
                                        'title_fontdict':{'y':1.05,
                                                          'fontsize': 18,
                                                          'fontweight':'bold'}})


# r = np.meshgrid(xrclusteredall.n_clusters.astype(str).values)
r = xrclustfinal.n_clusters.astype(str).values
# subtitles = [f'n-clusters={r.flatten()[i]}, ' + f'random state={c.flatten()[i]}' for i in range(c.size)]
subtitles = [f'n-clusters={r.flatten()[i]}, linkage=ward, metric=euclidean' for i in range(r.size)]

for i, ax in enumerate(fig.axes.flatten()):
    np.isnan(xr_States).plot.contour(ax=ax,
                                     transform=plot_maps.ccrs.PlateCarree(),
                                     linestyles=['solid'],
                                     colors=['black'],
                                     linewidths=2,
                                     levels=[0,1],
                                     add_colorbar=False)
    ax.add_feature(cfeature.NaturalEarthFeature(
        'cultural', 'admin_1_states_provinces_lines', '50m',
        edgecolor='grey', lw=1, facecolor='none'))
    ax.add_feature(cfeature.OCEAN)
    ax.add_feature(cfeature.LAKES)
    ax.add_feature(cfeature.COASTLINE)
    ax.set_ylabel(None) ; ax.set_xlabel(None)
    ax.set_title(subtitles[i], fontsize=12)

f_name = 'final_Hierchical_correlation_{}'.format(xrclustfinal.attrs['hash'])
path_fig = os.path.join(path_outmain, f_name)
plt.savefig(path_fig + '.pdf', bbox_inches='tight') # dpi auto 600

plt.savefig(path_fig + '.jpeg', bbox_inches='tight') # dpi auto 600







# Old stuff.
#%% Soy bean USDA

# raw_filename = '/Users/semvijverberg/Dropbox/VIDI_Coumou/Paper3_Sem/GDHY_MIRCA2000_Soy/USDA/usda_soy.nc'

# selbox = [250,290,28,50]
# ds = core_pp.import_ds_lazy(raw_filename, var='variable', selbox=selbox).rename({'z':'time'})
# ds.name = 'Soy_Yield'

# ds['time'] = pd.to_datetime([f'{y+1949}-01-01' for y in ds.time.values])
# ds.attrs['dataset'] = 'USDA'
# ds.attrs['planting_months'] = 'May/June'
# ds.attrs['harvest_months'] = 'October'

# ts = functions_pp.area_weighted(ds).mean(dim=('latitude', 'longitude')) # old, but silly to do area-weighted mean
# cl.store_netcdf(ts, filepath=
#                 '/Users/semvijverberg/Dropbox/VIDI_Coumou/Paper3_Sem/GDHY_MIRCA2000_Soy/USDA/usda_soy_spatial_mean_ts.nc')
#%% Maize yield USDA (unused)

# raw_filename = os.path.join('/Users/semvijverberg/surfdrive/VU_Amsterdam/GDHY_MIRCA2000_Soy/USDA/usda_maize.nc')

# ds = core_pp.import_ds_lazy(raw_filename)['variable'].rename({'z':'time'})
# ds.name = 'Maize_Yield'

# ds['time'] = pd.to_datetime([f'{y+1949}-01-01' for y in ds.time.values])
# ds.attrs['dataset'] = 'USDA'
# ds.attrs['planting_months'] = 'May/June'
# ds.attrs['harvest_months'] = 'October'

# ts = functions_pp.area_weighted(ds).mean(dim=('latitude', 'longitude'))
# ts_std = (ts - ts.mean()) / ts.std()
# ts_std.plot()
# #%%
# ds_std = (ds - ds.mean(dim='time')) / ds.std(dim='time')
# ts_ds_std = ds_std.mean(dim=('latitude', 'longitude'))
# #%%
# f, ax = plt.subplots()
# ts_ds_std.plot(ax=ax, c='blue')
# ts_std.plot(ax=ax)
# #%%
# cl.store_netcdf(ts, filepath=
#                 os.path.join('/Users/semvijverberg/surfdrive/VU_Amsterdam/GDHY_MIRCA2000_Soy/USDA/usda_maize_spatial_mean_ts.nc'))

# #%%

# allways_data_mask = np.isnan(ds).mean(dim='time')==0
# ts_mask = ds.where(allways_data_mask).mean(dim=('latitude', 'longitude'))
# cl.store_netcdf(ts_mask, filepath=
#                 '/Users/semvijverberg/Dropbox/VIDI_Coumou/Paper3_Sem/GDHY_MIRCA2000_Soy/USDA/usda_soy_spatial_mean_ts_allways_data.nc')
# #%%
# ano = ds - ds.mean(dim='time')
# plot_maps.plot_corr_maps(ano.isel(time=range(0,40,5)), row_dim='time', cbar_vert=.09)

#%% Years prior to 80s

raw_filename = os.path.join(root_data, 'masked_rf_gs_county_grids.nc')
selbox = [253,290,28,52] ; years = list(range(1950, 1973))

ds_avail = []
yrs_subsets = np.arange(1950,2020, 23)
yrs_subsets = [[1950, 1972], [1973, 1995], [1996, 2019]]

for yrs in yrs_subsets:
    years = list(range(yrs[0], yrs[1]))
    ds_raw = core_pp.import_ds_lazy(raw_filename, selbox=selbox)['variable'].rename({'z':'time'})
    ds_raw.name = 'Soy_Yield'
    ds_raw['time'] = pd.to_datetime([f'{y+1949}-01-01' for y in ds_raw.time.values])
    ds_raw = ds_raw.sel(time=core_pp.get_oneyr(ds_raw, *years))
    ds_avail.append((len(years) - np.isnan(ds_raw).sum(axis=0))/len(years))


ds_avail = xr.concat(ds_avail, dim='time')
ds_avail['time'] = ('time', [f'{y[0]}-{y[1]}' for y in yrs_subsets])
ds_avail = ds_avail.where(ds_avail.mean(dim='time')!=0)
#%%
# cluspath = os.path.join(path_outmain, 'linkage_ward_nc2_dendo_lindetrendgc_a9943.nc')
cluspath = path_stored_cluster
dsclust = core_pp.import_ds_lazy(cluspath)
clusmask = (dsclust['xrclustered'] == 1).astype(int)

ds_avail = ds_avail.where(clusmask==1)

#%%
units = '% of datapoints (# dp / total # of years)'
plot_map = plot_maps.plot_corr_maps
fg = plot_map(ds_avail, **{'wspace':.05, 'hspace':.16, 'cbar_vert':-.08,
                           'col_dim':'time',
                            'zoomregion':selbox, 'cmap':plt.cm.inferno_r,
                            'x_ticks':np.array([260,270,280]),
                            'y_ticks':np.array([32, 37, 42, 47]),
                            'clevels':np.arange(0.,1, 0.05),
                            'units':units,
                            'title_fontdict':{'y':1.07,
                                             'fontsize': 18,
                                             'fontweight':'bold'}})


facecolorocean = '#caf0f8' ; facecolorland='white'
for ax in fg.fig.axes[:-1]:
    ax.add_feature(plot_maps.cfeature.__dict__['LAND'],
                   facecolor=facecolorland,
                   zorder=0)
    ax.add_feature(plot_maps.cfeature.__dict__['OCEAN'],
                   facecolor=facecolorocean,
                   zorder=0)

    cmp = ["3c096c","5a189a","7b2cbf","9d4edd","c77dff","e0aaff"]
    cmp = plot_maps.get_continuous_cmap(cmp,
                    float_list=list(np.linspace(0,1,5)))
    ax.contour(clusmask.longitude, clusmask.latitude,
               clusmask.values,
                levels=[0,.5, 1.],
               transform=plot_maps.ccrs.PlateCarree(),
               zorder=0, **{'linestyles':['solid'],
                              'colors':['red'],
                              'linewidths':0})
f_name = 'datapoints_over_time.jpg'
fg.fig.savefig(os.path.join(path_outmain, f_name), bbox_inches='tight', dpi=300)



# for i, ax in enumerate(fig.axes.flatten()):
#     np.isnan(xr_States).plot.contour(ax=ax,
#                                      transform=plot_maps.ccrs.PlateCarree(),
#                                      linestyles=['solid'],
#                                      colors=['black'],
#                                      linewidths=2,
#                                      levels=[0,1],
#                                      add_colorbar=False)
#     ax.add_feature(cfeature.NaturalEarthFeature(
#         'cultural', 'admin_1_states_provinces_lines', '50m',
#         edgecolor='grey', lw=1, facecolor='none'))
#     ax.add_feature(cfeature.OCEAN)
#     ax.add_feature(cfeature.LAKES)
#     ax.add_feature(cfeature.COASTLINE)
#     ax.set_ylabel(None) ; ax.set_xlabel(None)
#     ax.set_title(subtitles[i], fontsize=12)
