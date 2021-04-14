import os
import json
from laspy.file import File
from matplotlib.patches import Rectangle
import random
import matplotlib.pyplot as plt
import numpy as np

class RoiCropper(object):

    def __init__(self, path, filename):

        self.path = path
        self.filename = filename

    def visualizer(self, downsample_rate = 0.01):

        if not os.path.exists(self.path + 'field_metadata.json'):

            #Define ROI area
            coords = {'x_min': 0, 'x_max': 0, 'y_min': 0, 'y_max': 0}
            #Save plots metadata to JSON
            with open(self.path + 'field_metadata.json', "w") as write_file: json.dump(coords, write_file)


        with open(self.path + 'field_metadata.json', "r") as read_file: coords = json.load(read_file)

        #Import point cloud
        area_las = File(self.path + self.filename, mode='r')
        X = area_las.x-area_las.header.min[0]
        Y = area_las.y-area_las.header.min[1]
        Z = area_las.z-area_las.header.min[2]

        points = np.vstack((X,Y,Z)).transpose()

        #Crop area with rectangle
        field = points[(points[:,0] >= coords['x_min']) & (points[:,0] < coords['x_max']) & (points[:,1] >= coords['y_min']) & (points[:,1] < coords['y_max'])]

        outFile = File(self.path + "field.las", mode = "w", header = area_las.header)
        outFile.x = field[:,0] + area_las.header.min[0]
        outFile.y = field[:,1] + area_las.header.min[1]
        outFile.z = field[:,2] + area_las.header.min[2]
        outFile.close()

        #Visualize
        indexes = random.sample(range(0, points.shape[0]), round(points.shape[0]*downsample_rate))

        fig = plt.figure(figsize=[15, 10])
        ax = plt.axes()

        ax.scatter(points[indexes,0], points[indexes,1], c = points[indexes,1]*points[indexes,2], s = 0.01, marker='o')

        ax.add_patch(Rectangle(xy=(coords['x_min'], coords['y_min']), width = coords['x_max']-coords['x_min'], height=coords['y_max']-coords['y_min'], linewidth=1, color='red', fill=False))

        ax.axis('equal')
        plt.show()




if __name__ == '__main__':

    RC = RoiCropper('/Users/michal/Desktop/Dev/Data/Lidar/20/', 'lidar_20.las')
    RC.visualizer()