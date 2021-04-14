import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection, Line3DCollection
import json
from laspy.file import File
import numpy as np
from utils import rotate_points
import random
import warnings
warnings.filterwarnings("ignore")

class SubplotBordersVisualizer(object):

    def __init__(self,path, filename):

        self.path = path
        self.filename = filename


    def visualizer(self, downsample_rate = 0.2, top = False):

        plot_las = File(self.path + 'plots/' + self.filename, mode='r')
        fm = self.filename.split('_')
        x, y = fm[:2]
        with open(self.path + "plots/plots_metadata.json", "r") as read_file: data = json.load(read_file)
        with open(self.path + "subplots/{}_{}_metadata.json".format(x,y), "r") as read_file: plot_data = json.load(read_file)

        #Get point clouds
        X = plot_las.x
        Y = plot_las.y
        Z = plot_las.z

        points = np.vstack((X,Y,Z)).transpose()
        points_rot = rotate_points(points, data['rotation_angle'])
        coord = data['determinative_coordinate']
        borders = plot_data['borders']
        
        indexes = random.sample(range(0, points.shape[0]), round(points.shape[0]*downsample_rate))
        verts_side = []
        verts_top = []

        if not bool(coord):

            azimuth = 0
            xm = points_rot[:,0].min()
            xx = points_rot[:,0].max()
            zm = points_rot[:,2].min()
            zx = points_rot[:,2].max()

            for border in borders:

                verts_side.append([[xm, border, zm],[xm, border, zx]])
                verts_top.append([[xx, border, zx],[xm, border, zx]])

        if bool(coord):

            azimuth = 90
            ym = points_rot[:,1].min()
            yx = points_rot[:,1].max()
            zm = points_rot[:,2].min()
            zx = points_rot[:,2].max()


            for border in borders:

                verts_side.append([[border ,ym, zm],[border, ym, zx]])
                verts_top.append([[border, yx, zx],[border, ym, zx]])

        if top:

            fig = plt.figure(figsize=[15, 10])
            ax = plt.axes(projection='3d')
            ax.view_init(90,azimuth)
            ax.scatter(points_rot[indexes,0], points_rot[indexes,1], points_rot[indexes,2], c = points_rot[indexes,2] , s= 0.1, marker='o')

            for vert in verts_top: ax.add_collection3d(Poly3DCollection(vert, facecolors='white', linewidths=1, edgecolors='r', alpha=.20))
            
            ax.set_xlabel('x')
            ax.set_ylabel('y')
            ax.set_zlabel('z')
            plt.show()

        else:

            fig = plt.figure(figsize=[15, 10])
            ax = plt.axes(projection='3d')
            ax.view_init(0,azimuth)
            ax.scatter(points_rot[indexes,0], points_rot[indexes,1], points_rot[indexes,2], c = points_rot[indexes,2] , s= 0.1, marker='o')

            for vert in verts_side: ax.add_collection3d(Poly3DCollection(vert, facecolors='white', linewidths=1, edgecolors='r', alpha=.20))
            ax.set_xlabel('x')
            ax.set_ylabel('y')
            ax.set_zlabel('z')
            plt.show()

if __name__ == '__main__':

    SBV = SubplotBordersVisualizer('/Users/michal/Desktop/Dev/Data/Lidar/20/', '18.4_1.7_deterrained_field.las')
    SBV.visualizer()