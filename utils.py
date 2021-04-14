import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import argrelmax
import scipy
import warnings
warnings.filterwarnings("ignore")

def save_img(points: np.ndarray, filename: str, path: str, elevation: int, azimuth: int):

    if filename == 'classification':

        fig = plt.figure(figsize=[30, 20])
        ax = plt.axes(projection='3d')
        ax.view_init(elevation, azimuth)
        ax.scatter(points[:,0], points[:,1], points[:,2], c = points[:,3], s = 0.01, marker='o')
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        ax.set_zlabel('z')
        plt.savefig('{}{}.png'.format(path, filename))

    elif filename == 'edge':

        fig = plt.figure(figsize=[30, 20])
        ax = plt.axes(projection='3d')
        ax.view_init(elevation, azimuth)
        idxs = points[:,3] < np.quantile(points[:,3], 0.01)
        ax.scatter(points[idxs,0], points[idxs,1], points[idxs,2], c = 'red', s = 0.01, marker='o')
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        ax.set_zlabel('z')
        plt.savefig('{}{}.png'.format(path, filename))

    else:

        fig = plt.figure(figsize=[30, 20])
        ax = plt.axes(projection='3d')
        ax.view_init(elevation, azimuth)
        ax.scatter(points[:,0], points[:,1], points[:,2], c = points[:,2], s = 0.01, marker='o')
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        ax.set_zlabel('z')
        plt.savefig('{}{}.png'.format(path, filename))

def rotate_points(points: np.ndarray, angle:float):

    rotation_matrix = np.matrix([[np.cos(angle),-np.sin(angle)],[np.sin(angle),np.cos(angle)]])
    points_xy = points[:,0:2]*rotation_matrix 
    
    return np.array(np.hstack((points_xy, points[:,2].reshape(-1,1))))


def compute_projections(points: np.ndarray, division: float):

    projections_x = []
    projections_y = []
    x_loc = []
    y_loc = []

    bounds_x = np.linspace(int(np.floor(points[:,0].min())), int(np.floor(points[:,0].max())+1),
    round((1/division)*(int(np.floor(points[:,0].max())+1) - int(np.floor(points[:,0].min())))))

    for i, dirr in enumerate(bounds_x):

        if i > 0: 

            projections_x.append(points[(points[:,0] >= bounds_x[i-1]) & (points[:,0] < bounds_x[i]),2].sum())
            x_loc.append((bounds_x[i]+bounds_x[i-1])/2)


    bounds_y = np.linspace(int(np.floor(points[:,1].min())), int(np.floor(points[:,1].max())+1),
    round((1/division)*(int(np.floor(points[:,1].max())+1) - int(np.floor(points[:,1].min())))))

    for i, dirr in enumerate(bounds_y):

        if i > 0: 
            projections_y.append(points[(points[:,1] >= bounds_y[i-1]) & (points[:,1] < bounds_y[i]),2].sum())
            y_loc.append((bounds_y[i]+bounds_y[i-1])/2)
    
    return np.reshape(x_loc + projections_x, (2,len(projections_x))).T, np.reshape(y_loc + projections_y, (2,len(projections_y))).T

def compute_projection(points: np.ndarray, division: float, coord: int):

    projections = []
    loc = []

    bounds = np.linspace(int(np.floor(points[:,coord].min())), int(np.floor(points[:,coord].max())+1),
    round((1/division)*(int(np.floor(points[:,coord].max())+1) - int(np.floor(points[:,coord].min())))))

    for i, dirr in enumerate(bounds):

        if i > 0: 

            projections.append(points[(points[:,coord] >= bounds[i-1]) & (points[:,coord] < bounds[i]),2].sum())
            loc.append((bounds[i]+bounds[i-1])/2)
    
    return np.reshape(loc + projections, (2,len(projections))).T
    

def compute_signal(points: np.ndarray, division: float, coord: int):

    projections = []
    loc = []

    bounds = np.linspace(int(np.floor(points[:,coord].min())), int(np.floor(points[:,coord].max())+1),
    round((1/division)*(int(np.floor(points[:,coord].max())+1) - int(np.floor(points[:,coord].min())))))

    for i, dirr in enumerate(bounds):

        if i > 0: 

            sampled_points = points[(points[:,coord] >= bounds[i-1]) & (points[:,coord] < bounds[i])]
            if sampled_points.shape[0] > 0 :
                projections.append(sampled_points[:,2].sum()/sampled_points.shape[0])
                loc.append((bounds[i]+bounds[i-1])/2)
    
    return np.reshape(loc + projections, (2,len(projections))).T
    

def find_angle(points: np.ndarray,  detail_resolution: float):

    angles = []
    loss_value = []

    for angle in np.linspace(-np.pi/2,np.pi/2,360):

        angles.append(angle)

        rotated_points = rotate_points(points, angle)

        px, py  = compute_projections(rotated_points, division = detail_resolution)

        loss_value.append(-(np.var(px[:,1]) + np.var(py[:,1])))

    resmat = np.reshape(angles + loss_value, (2,len(angles))).T

    return resmat[np.argmin(resmat[:,1]),0]

def fit_sin(tt, yy):
    '''Fit sin to the input time sequence, and return fitting parameters "amp", "omega", "phase", "offset", "freq", "period" and "fitfunc"'''

    tt = np.array(tt)
    yy = np.array(yy)

    ff = np.fft.fftfreq(len(tt), (tt[1]-tt[0]))   # assume uniform spacing
    Fyy = abs(np.fft.fft(yy))

    guess_freq = abs(ff[np.argmax(Fyy[1:])+1])   # excluding the zero frequency "peak", which is related to offset
    guess_amp = np.std(yy) * 2.**0.5
    guess_offset = np.mean(yy)
    guess = np.array([guess_amp, 2.*np.pi*guess_freq, 0., guess_offset])

    def sinfunc(t, A, w, p, c):  return A * np.sin(w*t + p) + c

    popt, pcov = scipy.optimize.curve_fit(sinfunc, tt, yy, p0=guess)
    A, w, p, c = popt
    f = w/(2.*np.pi)
    fitfunc = lambda t: A * np.sin(w*t + p) + c

    return {"amp": A, "omega": w, "phase": p, "offset": c, "freq": f, "period": 1./f, "fitfunc": fitfunc, "maxcov": np.max(pcov), "rawres": (guess,popt,pcov)}


def determine_plots_orientation(x_projection, y_projection):

    if np.var(x_projection) > np.var(y_projection): return 0
    else: return 1


def evaluate_plot_seeds(points: np.ndarray, detail_resolution: float):

    px, py =  compute_projections(points, detail_resolution)
    coord = determine_plots_orientation(px[:,1], py[:,1])

    pr =  compute_projection(points, detail_resolution, coord)
    sinf = fit_sin(pr[:,0], pr[:,1])
    sinf_eval = sinf["fitfunc"](pr[:,0])

    seeds_coord = pr[argrelmax(sinf_eval),0].reshape(-1,1)

    return seeds_coord.reshape(-1), coord

def find_plot_seeds(points: np.ndarray, plots_num: int):

    seeds_num = 0 
    resolution = 0
    seeds = np.array([])

    while seeds_num != plots_num and resolution <= 1:

        resolution += 0.05

        seeds_coord, coord = evaluate_plot_seeds(points, detail_resolution = resolution)
        seeds_num = seeds_coord.shape[0]

    projection = compute_projection(points, resolution, int(not bool(coord)))

    if not coord: seeds = np.reshape(list(seeds_coord) + list(np.repeat(projection[np.argmax(projection[:,1]),0], plots_num)), (2, plots_num)).T
    elif coord: seeds = np.reshape(list(np.repeat(projection[np.argmax(projection[:,1]),0], plots_num)) + list(seeds_coord), (2, plots_num)).T

    return seeds, resolution, coord

def clean_edge_noise(points: np.ndarray, resolution: float, coord: int):

    projection = compute_projection(points, resolution, coord)
    left_part = projection[projection[:,0] <= np.mean(projection[:,0]),:]
    right_part = projection[projection[:,0] > np.mean(projection[:,0]),:]

    left_peak = left_part[np.argmax(left_part[:,1]),:]
    right_peak = right_part[np.argmax(right_part[:,1]),:]

    adjust = ((right_peak[0] - left_peak[0])*0.1)/2

    left_boarder = left_peak[0] + adjust
    right_boarder = right_peak[0] - adjust

    return points[(points[:, coord] > left_boarder) & (points[:, coord] < right_boarder),:]