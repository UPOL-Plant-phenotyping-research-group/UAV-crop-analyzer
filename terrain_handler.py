import numpy as np
from geomdl import BSpline
from geomdl import utilities
from geomdl.visualization import VisMPL
from sklearn.neighbors import KDTree
from laspy.file import File
import random
from matplotlib import cm
import matplotlib.pyplot as plt
from utils import save_img
import os

class TerrainHandler:

    def __init__(self, lasFile_path, filename, downsampling_rate = 1, visualize = True):

        self.path = lasFile_path
        self.filename = filename
        self.dw_rate = downsampling_rate
        self.lasFile = File(self.path+self.filename, mode='r')
        self.points = np.vstack((self.lasFile.x - self.lasFile.header.min[0],self.lasFile.y - self.lasFile.header.min[1],self.lasFile.z - self.lasFile.header.min[2])).transpose()
        self.point_cloud = self.points[random.sample(range(0,self.points.shape[0]), round(self.points.shape[0]*self.dw_rate)),:]
        self.visualize = visualize
        

    def sliding_window(self, points: np.ndarray, stepSize: int, windowSize: int):
	
        # slide a window across the x-y hyperplane
        for x in range(int(np.floor(points[:,0].min())), int(np.ceil(points[:,0].max())), stepSize):
            for y in range(int(np.floor(points[:,1].min())), int(np.ceil(points[:,1].max())), stepSize):
                # yield the current window
                yield (points[(points[:,0] >= x) & (points[:,0] < x+windowSize) & (points[:,1] >= y) & (points[:,1] < y+windowSize)])


    def outlier_detector(self, points: np.ndarray, metric = 'minkowski', method = 'perimeter', deviance = 3.5, radius = 0.5, K = 50):

        assert method == 'perimeter' or method == 'nn' or method == 'KDTree', 'Method argument has to be perimeter (neighbors are in given distance far away from examined point) or nn (fixed number of closest (given by metric) neigbors is taken) or  KDTree (neighborhood is K closest points given by KDTree)'

        neigbor_dist = []
        neighborhood_size_flag = []

        tree = KDTree(points[:,:2], metric = metric)

        for i, point in enumerate(points):

            if method == 'nn': 

                _, index = tree.query(point[:2].reshape(1, -1), k = K+1)
                index = index[0]
                neighbors = points[index,:]

            elif method == 'perimeter':

                index = tree.query_radius(point[:2].reshape(1, -1), radius)[0]
                neighbors = points[index, :]

                if neighbors.shape[0] < 5: neighborhood_size_flag.append(i)
        
            point_frame = np.repeat(point.reshape(1,-1), repeats = neighbors.shape[0], axis=0)
            mean_dist = np.mean(np.abs(neighbors[: , 2] - point_frame[: , 2]))

            neigbor_dist.append(mean_dist)

        neigbor_dist = np.array(neigbor_dist)
        flag = neigbor_dist < neigbor_dist.mean() + deviance*neigbor_dist.var()**(0.5)
        flag[neighborhood_size_flag] = False

        return flag


    def filter_terrain_points(self, points: np.ndarray, method: str, window_size: int, window_stride: int, k_values: int, window_quantile: float):

        assert method == 'quantile' or method == 'k-values', 'Method argument has to be quantile (only given percentage of lowest points are selected) or k-values (k-lowest-values are selected) for terrain model'

        terrain_points = []

        for area in self.sliding_window(points, stepSize=window_stride, windowSize=window_size):

            if method == 'quantile' and area.shape[0] > 0: terrain_points.append(area[np.quantile(area[:,2], window_quantile) >= area[:,2],:])


            elif method == 'k-values' and area.shape[0] >= k_values:
        
                part = np.argpartition(area[:,2], k_values)
                terrain_points.append(area[part[:k_values],:])

            elif method == 'k-values' and area.shape[0] < k_values:

                terrain_points.append(area)
            
        return np.unique(np.vstack(terrain_points), axis=0)


    def create_terrain_grid(self, points: np.ndarray, metric='minkowski', K = 50, grid_resolution = 100):

        terrain_grid = []
        tree = KDTree(points[:,:2], metric = metric)

        x_min = np.floor(points[:,0].min())
        x_max = np.ceil(points[:,0].max())
        y_min = np.floor(points[:,1].min())
        y_max = np.ceil(points[:,1].max())

        for x in np.linspace(x_min, x_max, grid_resolution).tolist():

            for y in np.linspace(y_min, y_max, grid_resolution).tolist():

                point = np.array([x,y])

                _, index = tree.query(point.reshape(1, -1), k = K+1)
                index = index[0]
                terrain_grid.append([x,y,points[index,2].mean()])

        return np.array(terrain_grid)

    def surface_fit(self, terrain_grid, grid_resolution = 100, u_degree = 2, v_degree = 2, delta = 0.01):

        # Create a BSpline surface instance
        surf = BSpline.Surface()

        # Set evaluation delta
        surf.delta = delta

        # Set up the surface
        surf.degree_u = u_degree
        surf.degree_v = v_degree

        control_points = terrain_grid.tolist()
        surf.set_ctrlpts(control_points, grid_resolution, grid_resolution)

        surf.knotvector_u = utilities.generate_knot_vector(surf.degree_u, grid_resolution)
        surf.knotvector_v = utilities.generate_knot_vector(surf.degree_v, grid_resolution)

        # Evaluate surface points
        surf.evaluate()

        return surf

    def _execute(self):

        print('Process of field surface evaluation started')
        
        if not os.path.exists(self.path + 'surface_evaluation/'): os.makedirs(self.path + 'surface_evaluation/')
        
        out_flag = self.outlier_detector(self.point_cloud, method = 'nn', metric = 'minkowski', radius = 0.2, deviance = 3, K = 50)
        
        outFile = File(self.path  + 'surface_evaluation/' + "clean_field.las", mode = "w",header = self.lasFile.header)
        outFile.x = self.point_cloud[out_flag,0] + self.lasFile.header.min[0]
        outFile.y = self.point_cloud[out_flag,1] + self.lasFile.header.min[1]
        outFile.z = self.point_cloud[out_flag,2] + self.lasFile.header.min[2]
        outFile.close()

        save_img(self.point_cloud[out_flag,:],'clean_field_0_0', self.path + 'surface_evaluation/', 0, 0)
        save_img(self.point_cloud[out_flag,:],'clean_field_0_90', self.path + 'surface_evaluation/', 0, 90)
        
        print('outliers removed .....')
        terrain_points = self.filter_terrain_points(self.point_cloud[out_flag,:], method = 'quantile', window_size = 10, window_stride = 2, window_quantile = 0.01, k_values = 30)
        print('terrain points founded .....')
        terrain_grid = self.create_terrain_grid(terrain_points, metric='minkowski', K = 50, grid_resolution = 100)
        print('terrain grid was formed .....')

        surface = self.surface_fit(terrain_grid)
        # Create a visualization configuration instance with no legend, no axes and set the resolution to 120 dpi
        vis_config = VisMPL.VisConfig(ctrlpts = False, axes_equal = False)
        # Create a visualization method instance using the configuration above
        vis_obj = VisMPL.VisSurface(vis_config)
        # Set the visualization method of the curve object
        surface.vis = vis_obj
        surface.render(filename = self.path + 'surface_evaluation/' + "terrain.png", colormap = cm.cool, plot=False)
        print('surface was modeled .....')

        deTerreained_points = []

        # Get the evaluated points
        surface_points = np.array(surface.evalpts)

        for point in self.point_cloud[out_flag,:]:

            clean_point = point.copy()
            point_dist = np.array(((surface_points[:,0]-point[0])**2 + (surface_points [:,1]-point[1])**2)**(0.5))

            clean_point[2] = clean_point[2] - surface_points[np.argmin(point_dist),2]
            deTerreained_points.append(clean_point)

        deTerreained_points = np.array(deTerreained_points)
        deTerreained_points[:,2] = deTerreained_points[:,2] + np.abs(deTerreained_points[:,2].min())


        outFile = File(self.path + 'surface_evaluation/' + "deterrained_field.las", mode = "w",header = self.lasFile.header)
        outFile.x = deTerreained_points[:,0] + self.lasFile.header.min[0]
        outFile.y = deTerreained_points[:,1] + self.lasFile.header.min[1]
        outFile.z = deTerreained_points[:,2] + self.lasFile.header.min[2]
        outFile.close()

        save_img(deTerreained_points,'deterrained_field_0_0', self.path + 'surface_evaluation/', 0, 0)
        save_img(deTerreained_points,'deterrained_field_0_90', self.path + 'surface_evaluation/', 0, 90)

        print('point cloud was de-terrained ......')
        #return deTerreained_points

if __name__ == '__main__':

    TH = TerrainHandler('/Users/michal/Desktop/Dev/Data/Lidar/20/', 'field_20.las')
    TH._execute()