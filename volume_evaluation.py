import numpy as np
from geomdl import BSpline
from geomdl import utilities
from geomdl.visualization import VisMPL
from sklearn.neighbors import KDTree
from matplotlib import cm
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore")

class VolumeEvaluator(object):

    #Median method -  as a reference height in given interval, median of raw points z-coordinate is taken
    #Surface method - NURBS surface fit is used to model surface of given field, in given interval median of z-coordinate of surface points is taken as reference height

    def __init__(self, points: np.ndarray, area_size: float, method: str, surface_resolution: int, visualize: bool):

        assert (method == 'raw') or (method == 'surface'), 'Method of volume evaluation has to be median or surface'

        self.points = points
        self.area_size = area_size
        self.surface_resolution = surface_resolution
        self.method = method
        self.visualize = visualize


    def sliding_window(self, points: np.ndarray, stepSize: float, windowSize: float):
            # slide a window across the x-y hyperplane
            for x in np.arange(int(np.floor(points[:,0].min())), int(np.ceil(points[:,0].max())), stepSize):
                for y in np.arange(int(np.floor(points[:,1].min())), int(np.ceil(points[:,1].max())), stepSize):
                    # yield the current window
                    yield (points[(points[:,0] >= x) & (points[:,0] < x+windowSize) & (points[:,1] >= y) & (points[:,1] < y+windowSize)])


    def create_terrain_grid(self, points: np.ndarray, metric='minkowski', K = 10, grid_resolution = 100):

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

    def surface_visualizer(self, surface):

        #%matplotlib

        # Create a visualization configuration instance with no legend, no axes and set the resolution to 120 dpi
        vis_config = VisMPL.VisConfig(ctrlpts = False, axes_equal = False)
        # Create a visualization method instance using the configuration above
        vis_obj = VisMPL.VisSurface(vis_config)
        # Set the visualization method of the curve object
        surface.vis = vis_obj
        surface.render(colormap = cm.cool, plot=False)


    def compute_volume(self, points: np.ndarray, area_size: float):

        volume = 0

        for area in self.sliding_window(points, stepSize=area_size, windowSize=area_size):
            if area.shape[0]: volume += np.median(area[:,2]) * area_size**2

        return volume

    def _execute(self):

        VOLUME = 0

        if self.method == 'raw':

            VOLUME = self.compute_volume(self.points, self.area_size)

        elif self.method == 'surface':

            grid = self.create_terrain_grid(self.points, metric='minkowski', K = 10, grid_resolution = self.surface_resolution)
            surface = self.surface_fit(grid, grid_resolution = self.surface_resolution, u_degree = 2, v_degree = 2, delta = 0.01)

            VOLUME = self.compute_volume(np.array(surface.evalpts), self.area_size)

            if self.visualize: self.surface_visualizer(surface)

        return VOLUME