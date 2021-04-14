from utils import compute_signal, rotate_points
from fourier import get_peaks
import json
from laspy.file import File
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection, Line3DCollection
import random
import os
import numpy as np
import warnings
warnings.filterwarnings("ignore")
#https://www.pythonpool.com/matplotlib-draw-rectangle/


class SubplotDetector(object):

    def __init__(self, path, subplots_num):

        self.path = path
        self.subplots_num = subplots_num

    def visualize_subplot(self, points, borders, coord, x ,y, downsample_rate = 0.2, top = False):

        indexes = random.sample(range(0, points.shape[0]), round(points.shape[0]*downsample_rate))
        verts_side = []
        verts_top = []

        if not bool(coord):

            azimuth = 0
            xm = points[:,0].min()
            xx = points[:,0].max()
            zm = points[:,2].min()
            zx = points[:,2].max()

            for border in borders:

                verts_side.append([[xm, border, zm],[xm, border, zx]])
                verts_top.append([[xx, border, zx],[xm, border, zx]])

        if bool(coord):

            azimuth = 90
            ym = points[:,1].min()
            yx = points[:,1].max()
            zm = points[:,2].min()
            zx = points[:,2].max()


            for border in borders:

                verts_side.append([[border ,ym, zm],[border, ym, zx]])
                verts_top.append([[border, yx, zx],[border, ym, zx]])

        if top:

            fig = plt.figure(figsize=[30, 20])
            ax = plt.axes(projection='3d')
            ax.view_init(90,azimuth)
            ax.scatter(points[indexes,0], points[indexes,1], points[indexes,2], c = points[indexes,2] , s= 1, marker='o')

            for vert in verts_top: ax.add_collection3d(Poly3DCollection(vert, facecolors='white', linewidths=1, edgecolors='r', alpha=.20))

            plt.savefig(self.path + 'subplots/subplots_{}_{}.png'.format(x,y))

        else:

            fig = plt.figure(figsize=[30, 20])
            ax = plt.axes(projection='3d')
            ax.view_init(0,azimuth)
            ax.scatter(points[indexes,0], points[indexes,1], points[indexes,2], c = points[indexes,2] , s= 1, marker='o')

            for vert in verts_side: ax.add_collection3d(Poly3DCollection(vert, facecolors='white', linewidths=1, edgecolors='r', alpha=.20))

            plt.savefig(self.path + 'subplots/subplots_{}_{}.png'.format(x,y))


    def get_borders(self, points: np.ndarray, coord: int, subplots_num):

        projection = compute_signal(points, 0.01, int( not bool(coord)))

        mins, maxs = get_peaks(projection[:,0], projection[:,1], method = 'numpy')

        if mins[0] is None:

            mins, maxs = get_peaks(projection[:,0], projection[:,1], method = 'lm')
            print('Lm model used for fourier fit')

        else: print('Numpy model used for fourier fit')

        if mins[0].shape[0] == subplots_num + 1: borders = mins[0]
        elif mins[0].shape[0] == subplots_num:

            if (mins[0][0] > maxs[0][0]) and (mins[0][-1] > maxs[0][-1]): borders = [np.max([mins[0][0] - np.median(np.diff(mins[0])), points[:,int( not bool(coord))].min()])] + list(mins[0])

            elif (mins[0][0] < maxs[0][0]) and (mins[0][-1] < maxs[0][-1]): borders = list(mins[0]) + [np.min([mins[0][-1] + np.median(np.diff(mins[0])), points[:,int(not bool(coord))].max()])]

        else: borders = np.linspace(projection[:,0].min(), projection[:,0].max(), subplots_num+1)

        return borders

    def _execute(self, filename):

        print('Subplot localization in single plot started')
        if not os.path.exists(self.path + 'subplots/'): os.makedirs(self.path + 'subplots/')
        print('Data import')
        #Import las files of plot
        x, y,  ft_ = filename.split('_')
        plot_las = File(self.path + 'plots/' + filename, mode='r')
        dt_plot_las = File(self.path + 'plots/' + '{}_{}_deterrained_{}'.format(x, y, ft_))

        #Get point clouds
        X = plot_las.x
        Y = plot_las.y
        Z = plot_las.z
        points = np.vstack((X,Y,Z)).transpose()

        X = dt_plot_las.x
        Y = dt_plot_las.y
        Z = dt_plot_las.z
        dt_points = np.vstack((X,Y,Z)).transpose()
        
        #Import metadata
        with open(self.path + "plots/plots_metadata.json", "r") as read_file: data = json.load(read_file)
        coord = data['determinative_coordinate']
        rot_angle = data['rotation_angle']

        #rotate point clouds
        rot_points = rotate_points(points, rot_angle)
        rot_dt_points = rotate_points(dt_points, rot_angle)

        print('Borders detection')
        #compute borders
        borders = self.get_borders(rot_points, coord, self.subplots_num)

        #Define plots metadata
        metafile = {'x':x, 'y':y, 'determinative_coordinate': coord, 'rotation_angle': rot_angle, 'borders': borders}
        #Save plots metadata to JSON
        with open(self.path + 'subplots/{}_{}_metadata.json'.format(x, y), "w") as write_file: json.dump(metafile, write_file)
        #Visualize result of subplot detection
        self.visualize_subplot(rot_dt_points, borders, coord, x, y)
        print('{} plot was processed'.format(filename))

    def _execute_batch(self):

        print('Subplot localization of batch of plots started')
        if not os.path.exists(self.path + 'subplots/'): os.makedirs(self.path + 'subplots/')

        files = [file for file in os.listdir(self.path + 'plots/') if file.endswith('deterrained_field.las')]
        
        #Import metadata
        with open(self.path + "plots/plots_metadata.json", "r") as read_file: data = json.load(read_file)
        coord = data['determinative_coordinate']
        rot_angle = data['rotation_angle']

        for file in files:

            #Import las files of plot
            x, y, _, ft = file.split('_')
            plot_las = File(self.path + 'plots/' + '{}_{}_{}'.format(x, y, ft))
            dt_plot_las = File(self.path + 'plots/' + file, mode='r')

            #Get point clouds
            X = plot_las.x
            Y = plot_las.y
            Z = plot_las.z
            points = np.vstack((X,Y,Z)).transpose()

            X = dt_plot_las.x
            Y = dt_plot_las.y
            Z = dt_plot_las.z
            dt_points = np.vstack((X,Y,Z)).transpose()


            #rotate point clouds
            rot_points = rotate_points(points, rot_angle)
            rot_dt_points = rotate_points(dt_points, rot_angle)

            #compute borders
            borders = self.get_borders(rot_points, coord, self.subplots_num)

            #Define plots metadata
            metafile = {'x':x, 'y':y, 'determinative_coordinate': coord, 'rotation_angle': rot_angle, 'borders': list(borders)}
            #Save plots metadata to JSON
            with open(self.path + 'subplots/{}_{}_metadata.json'.format(x, y), "w") as write_file: json.dump(metafile, write_file)
            #Visualize result of subplot detection
            self.visualize_subplot(rot_dt_points, borders, coord, x, y)
            print('{} plot was processed'.format(file))

if __name__ == '__main__':

    #SD = SubplotDetector('/Users/michal/Desktop/Dev/Data/Lidar/20/', 53)
    #SD._execute('6.6_1.7_field.las')
    SD = SubplotDetector('/Users/michal/Desktop/Dev/Data/Lidar/20/', 53)
    SD._execute_batch()