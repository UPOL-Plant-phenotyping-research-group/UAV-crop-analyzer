import numpy as np
from laspy.file import File
import json
from volume_evaluation import VolumeEvaluator
import pandas as pd
import os
from utils import rotate_points
import warnings
warnings.filterwarnings("ignore")


class ComputeFieldStats(object):

    def __init__(self, path, major_border_pct = 0.05, minor_border_pct = 0.01, height_quantile = 0.2, height_threshold = 0.3):

        self.path = path
        self.major_border_pct = major_border_pct
        self.minor_border_pct = minor_border_pct
        self.height_quantile = height_quantile
        self.height_threshold = height_threshold


    def cut_border(self, points: np.ndarray, coord: int, major_border_pct: float, minor_border_pct: float):

        major_adjuster = (points[:,coord].max() - points[:,coord].min()) * major_border_pct
        minor_adjuster = (points[:,int(not bool(coord))].max() - points[:,int(not bool(coord))].min()) * minor_border_pct

        return points[(points[:,coord] > points[:,coord].min()+major_adjuster) & (points[:,coord] < points[:,coord].max()-major_adjuster) & (points[:,int(not bool(coord))] > points[:,int(not bool(coord))].min()+minor_adjuster) & (points[:,int(not bool(coord))] < points[:,int(not bool(coord))].max()-minor_adjuster),:]

    def filter_low_points(self, points: np.ndarray, method: str, height_quantile: float, height_threshold: float):

        if method == 'quantile': return points[points[:,2] > np.quantile(points[:,2], height_quantile),:]
        elif method == 'threshold': return points[points[:,2] > height_threshold,:]

    def _execute_single_field(self, filename):

        if not os.path.exists(self.path+'structured_results/'): os.makedirs(self.path+'structured_results/')

        structured_data = []

        print('{} IS BEING PROCESSED'.format(filename))
        print('Data import')

        with open(self.path + "plots/plots_metadata.json", "r") as read_file: plot_data = json.load(read_file)
        coord = plot_data['determinative_coordinate']
        rot_angle = plot_data['rotation_angle']

        with open(self.path + 'subplots/' + filename, "r") as read_file: subplot_data = json.load(read_file)
        plot_las = File(self.path+ 'plots/' + '{}_{}_deterrained_field.las'.format(subplot_data['x'], subplot_data['y']))

        #Get point clouds
        X = plot_las.x
        Y = plot_las.y
        Z = plot_las.z - plot_las.header.min[2]
        points = np.vstack((X,Y,Z)).transpose()

        rot_points = rotate_points(points, rot_angle)
        borders = subplot_data['borders']

        print('Subplots evaluation')
        for i in range(0, len(borders)-1):

            subfield = rot_points[(rot_points[:,int(not bool(coord))] > borders[i]) & (rot_points[:,int(not bool(coord))] < borders[i+1]),:]

            cropped_subfield = self.cut_border(subfield, coord, self.major_border_pct, self.minor_border_pct)

            cleaned_subfield  = self.filter_low_points(cropped_subfield, method = 'quantile', height_quantile=0.2, height_threshold=0.3)

            VE = VolumeEvaluator(cleaned_subfield, 0.1, 'raw', 100, False)
            growth_stat = VE._execute()
            
            unrot_subfield = rotate_points(subfield, -rot_angle)

            x_min = unrot_subfield[:,0].min()
            x_max = unrot_subfield[:,0].max()
            y_min = unrot_subfield[:,1].min()
            y_max = unrot_subfield[:,1].min()

            center_x = np.mean(unrot_subfield[:,0])
            center_y = np.mean(unrot_subfield[:,1])

            plot_size = (borders[i+1]-borders[i]) * (subfield[:,coord].max() - subfield[:,coord].min())

            structured_data.append(dict(zip(('filename', 'x_min', 'x_max', 'y_min', 'y_max','x_center','y_center', 'plot_size', 'raw_point_num', 'clean_point_num', 'volume'),(filename, x_min, x_max, y_min, y_max, center_x, center_y, plot_size, subfield.shape[0], cleaned_subfield.shape[0], growth_stat))))

            print('{} of {} subplots were evaluated'.format(i+1, len(borders)-1))

        df = pd.DataFrame(structured_data)
        df = df[['filename', 'x_min', 'x_max', 'y_min', 'y_max','x_center','y_center', 'plot_size', 'raw_point_num', 'clean_point_num', 'volume']]
        df.to_excel(self.path + 'structured_results/' + '/{}_{}_result.xlsx'.format(subplot_data['x'],subplot_data['y']), engine='openpyxl')
        print('Plot was succesfully analyzed and structured dataframe {}_{}_result.xlsx exported'.format(subplot_data['x'],subplot_data['y']))

    def _execute_field_batch(self):

        if not os.path.exists(self.path+'structured_results/'): os.makedirs(self.path+'structured_results/')

        files = [file for file in os.listdir(self.path + 'subplots/') if file.endswith('json')]

        with open(self.path + "plots/plots_metadata.json", "r") as read_file: plot_data = json.load(read_file)

        coord = plot_data['determinative_coordinate']
        rot_angle = plot_data['rotation_angle']

        for file in files:

            print('{} IS BEING PROCESSED'.format(file))
            print('Data import')
        
            structured_data = []

            with open(self.path + 'subplots/' + file, "r") as read_file: subplot_data = json.load(read_file)
            plot_las = File(self.path+ 'plots/' + '{}_{}_deterrained_field.las'.format(subplot_data['x'], subplot_data['y']))

            #Get point clouds
            X = plot_las.x
            Y = plot_las.y
            Z = plot_las.z - plot_las.header.min[2]
            points = np.vstack((X,Y,Z)).transpose()

            rot_points = rotate_points(points, rot_angle)
            borders = subplot_data['borders']

            print('Subplots evaluation')
            for i in range(0, len(borders)-1):

                subfield = rot_points[(rot_points[:,int(not bool(coord))] > borders[i]) & (rot_points[:,int(not bool(coord))] < borders[i+1]),:]

                cropped_subfield = self.cut_border(subfield, coord, self.major_border_pct, self.minor_border_pct)

                cleaned_subfield  = self.filter_low_points(cropped_subfield, method = 'quantile', height_quantile=0.2, height_threshold=0.3)

                VE = VolumeEvaluator(cleaned_subfield, 0.1, 'raw', 100, False)
                growth_stat = VE._execute()
                
                unrot_subfield = rotate_points(subfield, -rot_angle)

                x_min = unrot_subfield[:,0].min()
                x_max = unrot_subfield[:,0].max()
                y_min = unrot_subfield[:,1].min()
                y_max = unrot_subfield[:,1].min()

                center_x = np.mean(unrot_subfield[:,0])
                center_y = np.mean(unrot_subfield[:,1])

                plot_size = (borders[i+1]-borders[i]) * (subfield[:,coord].max() - subfield[:,coord].min())

                structured_data.append(dict(zip(('filename', 'x_min', 'x_max', 'y_min', 'y_max','x_center','y_center', 'plot_size', 'raw_point_num', 'clean_point_num', 'volume'),(file, x_min, x_max, y_min, y_max, center_x, center_y, plot_size,subfield.shape[0], cleaned_subfield.shape[0], growth_stat))))
                print('{} of {} subplots were evaluated'.format(i+1, len(borders)-1))

            df = pd.DataFrame(structured_data)
            df = df[['filename', 'x_min', 'x_max', 'y_min', 'y_max','x_center','y_center', 'plot_size', 'raw_point_num', 'clean_point_num', 'volume']]
            df.to_excel(self.path + 'structured_results/' + '/{}_{}_result.xlsx'.format(subplot_data['x'],subplot_data['y']), engine='openpyxl')
            print('Plot was succesfully analyzed and structured dataframe {}_{}_result.xlsx exported'.format(subplot_data['x'],subplot_data['y']))


if __name__ == '__main__':

    CFS = ComputeFieldStats('/Users/michal/Desktop/Dev/Data/Lidar/20/')
    CFS._execute_field_batch()
    #CFS._execute_single_field('6.6_1.7_metadata.json')