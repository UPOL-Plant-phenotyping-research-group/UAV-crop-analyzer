#%%
import os
import json
from laspy.file import File
from matplotlib.patches import Rectangle
import random
import matplotlib.pyplot as plt
import numpy as np
# %%
PATH = '/Users/michal/Desktop/Dev/Data/Lidar/20/lidar_20.las'

input_las = File(PATH, mode='r')

X = input_las.x-input_las.header.min[0]
Y = input_las.y-input_las.header.min[1]
Z = input_las.z-input_las.header.min[2]

points = np.vstack((X,Y,Z)).transpose()
downsample_rate = 0.01
indexes = random.sample(range(0, points.shape[0]), round(points.shape[0]*downsample_rate))

# %%
fig = plt.figure(figsize=[30, 20])
ax = plt.axes()

ax.scatter(points[indexes,0], points[indexes,1], c = points[indexes,1]*points[indexes,2], s = 0.01, marker='o')

ax.add_patch(Rectangle(xy=(223.5, 57), width=65, height=93, linewidth=1, color='red', fill=False))
ax.axis('equal')
#plt.savefig('/Users/michal/Desktop/Dev/Data/Lidar/Tutorial/ROI.png')
plt.show()