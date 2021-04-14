import numpy as np
import random
import os, sys
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from laspy.file import File
from utils import find_angle, rotate_points, compute_projections, compute_projection, determine_plots_orientation
from matplotlib.patches import Rectangle
import matplotlib.colors as mcolors
import json
import warnings
warnings.filterwarnings("ignore")

class PlotDetector(object):

    def __init__(self, path, plot_num, resolution, reprocessing_mode = False):

        self.path = path
        self.plot_num = plot_num
        self.resolution = resolution
        self.mode = reprocessing_mode

    #function for creation of chunks (for plots color specification)
    def chunkIt(self, seq, num):

        avg = len(seq) / float(num)
        chunks = []
        last = 0.0

        while last < len(seq):
            chunks.append(seq[int(last):int(last + avg)])
            last += avg

        return chunks


    def get_colors(self):

        # Sort colors by hue, saturation, value and name.
        by_hsv = sorted((tuple(mcolors.rgb_to_hsv(mcolors.to_rgb(color))),
                            name, color)
                            for name, color in mcolors.CSS4_COLORS.items())

        #get colors and its codes
        color_names = [(name, color) for hsv, name, color in by_hsv]

        #create chunks
        chunks = self.chunkIt(color_names, self.plot_num)

        colors = []
        #sample random colors for plots
        for i in range(0, self.plot_num): colors.append(random.sample(chunks[i], 1))

        return colors


    def write_las(self, points:np.ndarray, x:float, y:float, filename:str, header):

        outFile = File(self.path + 'plots/' + "{}_{}_{}.las".format(x, y, filename), mode = "w", header = header)
        outFile.x = points[:,0] + header.min[0]
        outFile.y = points[:,1] + header.min[1]
        outFile.z = points[:,2] + header.min[2]
        outFile.close()

    def form_plots(self, boundaries, points, field, dt_field, angle, coord, las_header):

        plots = []

        #Get colors for plots visualizing
        colors = self.get_colors()

        #Loop all plots
        for i, boundary in enumerate(boundaries):

            #if y is determinative coordinate
            if coord:
                
                #define plot metadata
                plots.append({'color': colors[i][0], 'x_min': boundary[2], 'x_max': boundary[3], 'y_min': boundary[0], 'y_max': boundary[1]})

                #crop plot from raw point cloud 
                f = field[(field[:,0] >= boundary[2]) & (field[:,0] < boundary[3]) & (field[:,1] >= boundary[0]) & (field[:,1] < boundary[1])]
                #crop plot from deterrained point cloud
                df = dt_field[(dt_field[:,0] >= boundary[2]) & (dt_field[:,0] < boundary[3]) & (dt_field[:,1] >= boundary[0]) & (dt_field[:,1] < boundary[1])]

                #Save cropped plot
                self.write_las(rotate_points(f, -angle), boundary[2], boundary[0], 'field', las_header)
                self.write_las(rotate_points(df, -angle), boundary[2], boundary[0], 'deterrained_field', las_header)

            #if x is determinative coordinate
            else:

                #define plot metadata
                plots.append({'color': colors[i][0], 'x_min': boundary[0], 'x_max': boundary[1], 'y_min': boundary[2], 'y_max': boundary[3]})
                #crop plot from raw point cloud
                f = field[(field[:,0] >= boundary[0]) & (field[:,0] < boundary[1]) & (field[:,1] >= boundary[2]) & (field[:,1] < boundary[3])]
                #crop plot from deterrained point cloud
                df = dt_field[(dt_field[:,0] >= boundary[0]) & (dt_field[:,0] < boundary[1]) & (dt_field[:,1] >= boundary[2]) & (dt_field[:,1] < boundary[3])]
                rotate_points(f, -angle)
                #Save cropped plot
                self.write_las(rotate_points(f, -angle), boundary[0], boundary[2], 'field', las_header)
                self.write_las(rotate_points(df, -angle), boundary[0], boundary[2], 'deterrained_field', las_header)

        #Define plots metadata
        metafile = {'determinative_coordinate': coord, 'rotation_angle': angle, 'plots': plots}
        #Save plots metadata to JSON
        with open(self.path + "plots/plots_metadata.json", "w") as write_file: json.dump(metafile, write_file)

        #Save plots visualization
        fig = plt.figure(figsize=[15, 20])
        ax = plt.axes()
        plt.set_cmap('jet')
        ax.scatter(points[:,0], points[:,1], c = points[:,2], s = 0.1, marker='o')

        for plot in plots:
            
            ax.add_patch(Rectangle(xy=(plot['x_min'], plot['y_min']), width=plot['x_max'] - plot['x_min'], height=plot['y_max'] - plot['y_min'], linewidth = 3, color = plot['color'][1], fill = False))
 
        ax.axis('equal')
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        plt.savefig(self.path +'plots/plot_boundaries.png')


    def reprocess_plots(self, data, points, field, dt_field, las_header, rotation_angle):

        for plot in data['plots']:
                
            #crop plot from raw point cloud 
            f = field[(field[:,0] >= plot['x_min']) & (field[:,0] < plot['x_max']) & (field[:,1] >= plot['y_min']) & (field[:,1] < plot['y_max'])]
            #crop plot from deterrained point cloud
            df = dt_field[(dt_field[:,0] >= plot['x_min']) & (dt_field[:,0] < plot['x_max']) & (dt_field[:,1] >= plot['y_min']) & (dt_field[:,1] < plot['y_max'])]

            #Save cropped plot
            self.write_las(rotate_points(f, -rotation_angle), plot['x_min'], plot['y_min'], 'field', las_header)
            self.write_las(rotate_points(df, -rotation_angle), plot['x_min'], plot['y_min'], 'deterrained_field', las_header)

        #Save plots visualization
        fig = plt.figure(figsize=[15, 20])
        ax = plt.axes()
        plt.set_cmap('jet')
        ax.scatter(points[:,0], points[:,1], c = points[:,2], s = 0.1, marker='o')

        for plot in data['plots']:
            
            ax.add_patch(Rectangle(xy=(plot['x_min'], plot['y_min']), width=plot['x_max'] - plot['x_min'], height=plot['y_max'] - plot['y_min'], linewidth = 3, color = plot['color'][1], fill = False))
 
        ax.set_xlim([points[:,0].min(), points[:,0].max()])
        ax.set_ylim([points[:,1].min(), points[:,1].max()])
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        ax.axis('equal')
        plt.savefig(self.path +'plots/plot_boundaries.png')


    def _execute(self):


        print('Import of point clouds')
        points = np.loadtxt(self.path + 'field_evaluation/labels.csv', delimiter=",")
        field_las = File(self.path + 'surface_evaluation/clean_field.las', mode='r')
        dt_field_las = File(self.path + 'surface_evaluation/deterrained_field.las', mode='r')

        points[:,0] = points[:,0] - field_las.header.min[0]
        points[:,1] = points[:,1] - field_las.header.min[1]
        points[:,2] = points[:,2] - field_las.header.min[2]

        X = field_las.x-field_las.header.min[0]
        Y = field_las.y-field_las.header.min[1]
        Z = field_las.z-field_las.header.min[2]
        field = np.vstack((X,Y,Z)).transpose()

        X = dt_field_las.x-field_las.header.min[0]
        Y = dt_field_las.y-field_las.header.min[1]
        Z = dt_field_las.z-field_las.header.min[2]
        dt_field = np.vstack((X,Y,Z)).transpose()

        if not self.mode:

            print('PLOT DETECTION STARTED')
            print('##################################################################')
            if not os.path.exists(self.path + 'plots/'): os.makedirs(self.path + 'plots/')

            #Find optimal rotation of plots just with crop points
            print('Computation of optimal point cloud rotation')
            #angle = find_angle(points[points[:,3] == 1,:3], self.resolution)
            angle = 0.05688120403435537
            #Rotate point clouds with optimal angle
            points_rot = rotate_points(points, angle)
            field_rot = rotate_points(field, angle)
            dt_field_rot = rotate_points(dt_field, angle)

            print('Computation of plots boundaries')
            px,py = compute_projections(points_rot, self.resolution)
            coord = determine_plots_orientation(px,py)

            #In this part should be boarders of plots computed, now manual vaules are used
            boundaries = [(6.6, 16.6, 1.7, 86.7), (18.4, 28.4, 1.7, 86.7),(30.6, 40.6, 1.9, 86.9),(42.6, 52.6, 2.3, 87.3), (54.9, 64.9, 2.5, 87.5)]
            print('Formating and saving plot las files and visualization of boundaries')

            self.form_plots(boundaries, points_rot, field_rot, dt_field_rot, angle, coord, field_las.header)

        elif self.mode:

            print('PLOT REPROCESSING STARTED')
            print('##################################################################')

            with open(self.path + "plots/plots_metadata.json", "r") as read_file: data = json.load(read_file)

            points_rot = rotate_points(points, data['rotation_angle'])
            field_rot = rotate_points(field, data['rotation_angle'])
            dt_field_rot = rotate_points(dt_field, data['rotation_angle'])

            print('Formating and saving plot las files and visualization of boundaries')
            self.reprocess_plots(data, points_rot, field_rot, dt_field_rot, field_las.header, data['rotation_angle'])


if __name__ == '__main__':

    PD = PlotDetector('/Users/michal/Desktop/Dev/Data/Lidar/20/', 5, 0.25, False)
    PD._execute()