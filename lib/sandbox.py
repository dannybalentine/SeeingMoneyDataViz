"""Create a choropleth map of US mean 2 bedroom rent prices"""

import sys
from pathlib import Path

# add root path of the repo to our environment path
root_path = Path(f"{__file__}/../../").resolve().as_posix()



# import modules
import matplotlib
from matplotlib import pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.ticker import FuncFormatter
import pandas as pd
import geopandas as gpd
import seaborn as sns
from shapely.geometry import Polygon
import missingno as msno
import os


# import rental pricing data from csv
filepath = root_path+'/bin/csv_files/average_housing_cost_by_state.csv'

df = pd.read_csv(filepath)

# rename columns
df.rename(columns={
    'median home price':'median_home_price',
    'monthly rent (2 bed)':'monthly_rent_2_bed'
},inplace=True)

# specify column as an int (don't need decimals here)
df['monthly_rent_2_bed'] = df['monthly_rent_2_bed'].astype(int)




gdf = gpd.read_file(root_path+'/bin/cb_2018_us_state_5m')



gdf = gdf.merge(df,left_on='STUSPS',right_on='state')


alaska_gdf = gdf[gdf.state=='AK']
hawaii_gdf = gdf[gdf.state=='HI']

# clip alaska
polygon = Polygon([(-170,50),(-170,72),(-140, 72),(-140,50)])
alaska_gdf.clip(polygon).plot( color='lightblue', linewidth=0.8, edgecolor='0.8')

# clip hawaii
hipolygon = Polygon([(-161,0),(-161,90),(-120,90),(-120,0)])
hawaii_gdf.clip(hipolygon).plot(color='lightblue', linewidth=0.8, edgecolor='0.8')

visframe = gdf.to_crs({'init':'epsg:2163'})

# create figure and axes for with Matplotlib for main map
fig, ax = plt.subplots(1, figsize=(18, 14))
# remove the axis box from the main map
ax.axis('off')


# create map of all states except AK and HI in the main map axis
visframe[~visframe.state.isin(['HI','AK'])].plot(color='lightblue', linewidth=0.8, ax=ax, edgecolor='0.8')


# Add Alaska Axis (x, y, width, height)
akax = fig.add_axes([0.1, 0.17, 0.17, 0.16])   


# Add Hawaii Axis(x, y, width, height)
hiax = fig.add_axes([.28, 0.20, 0.1, 0.1])



print(gdf.monthly_rent_2_bed.describe())

# Apply this the gdf to ensure that all states are assigned colors by the same function
def makeColorColumn(gdf,variable,vmin,vmax):
    # apply a function to a column to create a new column of assigned colors & return full frame
    norm = mcolors.Normalize(vmin=vmin, vmax=vmax, clip=True)
    mapper = plt.cm.ScalarMappable(norm=norm, cmap=plt.cm.Greens)
    gdf['value_determined_color'] = gdf[variable].apply(lambda x: mcolors.to_hex(mapper.to_rgba(x)))
    return gdf


# set the value column that will be visualised
variable = 'monthly_rent_2_bed'

# make a column for value_determined_color in gdf
# set the range for the choropleth values with the upper bound the rounded up maximum value
vmin, vmax = gdf.monthly_rent_2_bed.min(), gdf.monthly_rent_2_bed.max() #math.ceil(gdf.pct_food_insecure.max())
# Choose the continuous colorscale "YlOrBr" from https://matplotlib.org/stable/tutorials/colors/colormaps.html
#colormap = "YlOrBr"
colormap = "Greens"
gdf = makeColorColumn(gdf,variable,vmin,vmax)

# create "visframe" as a re-projected gdf using EPSG 2163
visframe = gdf.to_crs({'init':'epsg:2163'})



# create figure and axes for Matplotlib
fig, ax = plt.subplots(1, figsize=(18, 14))
# remove the axis box around the vis
ax.axis('off')

# set the font for the visualization to Helvetica
hfont = {'fontname':'Helvetica'}

# add a title and annotation
ax.set_title('Add your figure title \n here', **hfont, fontdict={'fontsize': '42', 'fontweight' : '1'})

# Create colorbar legend
fig = ax.get_figure()
# add colorbar axes to the figure
# This will take some iterating to get it where you want it [l,b,w,h] right
# l:left, b:bottom, w:width, h:height; in normalized unit (0-1)
cbax = fig.add_axes([0.89, 0.21, 0.03, 0.31])   

cbax.set_title('Add your legend title \n here \n', **hfont, fontdict={'fontsize': '15', 'fontweight' : '0'})

# add color scale
sm = plt.cm.ScalarMappable(cmap=colormap, \
                 norm=plt.Normalize(vmin=vmin, vmax=vmax))
# reformat tick labels on legend
sm._A = []
#comma_fmt = FuncFormatter(lambda x, p: format(x/100, '.0%'))
comma_fmt = FuncFormatter(lambda x, p: format(x/100,'.0%'))
#fig.colorbar(sm, cax=cbax, format=comma_fmt)
fig.colorbar(sm, cax=cbax)
tick_font_size = 16
cbax.tick_params(labelsize=tick_font_size)
ax.annotate("Add a comment here \n and more here", xy=(0.22, .085), xycoords='figure fraction', fontsize=14, color='#555555')


# create map
# Note: we're going state by state here because of unusual coloring behavior when trying to plot the entire dataframe using the "value_determined_color" column
for row in visframe.itertuples():
    if row.state not in ['AK','HI']:
        vf = visframe[visframe.state==row.state]
        c = gdf[gdf.state==row.state][0:1].value_determined_color.item()
        vf.plot(color=c, linewidth=0.8, ax=ax, edgecolor='0.8')



# add Alaska
akax = fig.add_axes([0.1, 0.17, 0.2, 0.19])   
akax.axis('off')
# polygon to clip western islands
polygon = Polygon([(-170,50),(-170,72),(-140, 72),(-140,50)])
alaska_gdf = gdf[gdf.state=='AK']
alaska_gdf.clip(polygon).plot(color=gdf[gdf.state=='AK'].value_determined_color, linewidth=0.8,ax=akax, edgecolor='0.8')


# add Hawaii
hiax = fig.add_axes([.28, 0.20, 0.1, 0.1])   
hiax.axis('off')
# polygon to clip western islands
hipolygon = Polygon([(-160,0),(-160,90),(-120,90),(-120,0)])
hawaii_gdf = gdf[gdf.state=='HI']
hawaii_gdf.clip(hipolygon).plot(column=variable, color=hawaii_gdf['value_determined_color'], linewidth=0.8,ax=hiax, edgecolor='0.8')



fig.savefig(os.getcwd()+'/mean_2_bedroom.png',dpi=400, bbox_inches="tight")
# bbox_inches="tight" keeps the vis from getting cut off at the edges in the saved png
# dip is "dots per inch" and controls image quality.  Many scientific journals have specifications for this
# https://stackoverflow.com/questions/16183462/saving-images-in-python-at-a-very-high-quality