# UAV-crop-analyzer

## Authors
Michal Polak [1]

[1] Palacky Univ, Fac Sci, Laboratory of Growth Regulators, Olomouc 77900, Czech Republic

## Introduction

UAV-crop-analyzer is a software developed for purpose of growth analysis of various crops based on its height. This is a first version/prototype of software, which was developed in Python 3.9 programming language. Expected input for analyzer is point cloud in **las** format and it provides user in several steps with many results. Output of last module is structured csv file providing information about crop growth in experimental units. Software was prototyped with data generated with **Ricopter** UAV machine manufactured by **Riegl** enterprise. Since we didn't produce sufficient timelines measurement of our fields, software is designed to analyse single point cloud of field at this moment. In future we plan develop more complex analysis, processing whole batch of time-sorted point clouds of field. Crucial **UAV-crop-analyzer** assumption is that crop is growing in regular rectangular grid of plots and subplots (this structure will be explained more precisely later). **UAV-crop-analyzer** is composed of 6 independent modules and its goal is to compute growth statistics of subplots (experimental units), which represents crop variants in experiment. Advantage of software is that algorithms used in **UAV-crop-analyzer** are *unsupervised* and it's use is *semi-automated*. Each module have several parameters configurable by user, which effects final output of module. The goal is to reduce the number of configurable parameters as much as possible.


## Modules

Neighborhoods described in next sections are based on x-y axis.

### 1. Manual localization of Field/ROI
In first step user will use module **manual_field_localizer.py**. This module visualizes raw point cloud (with given downsampling rate) and generates **field_metadata.json** file. In **field_metadata.json** file user will define x-y coordinates of rectangle corners (ROI/filed). User should define ROI i as small as possible around field, so unnecessary noisy points are not included.

![alt text](https://github.com/UPOL-Plant-phenotyping-research-group/UAV-crop-analyzer/blob/main/readme_images/ROI.png?raw=true)

### 2. Field preprocessing
In next part of pipeline, user will call **terrain_handler.py** module. This module performs two essential preprocessing steps Outliers removal and Terrain effect removal and prepares point cloud of field for further analysis.

As a first outliers are detected and removed from point cloud. For each point is computed local neigborhood (*radius* or *k-nearest neighbors*) and mean distance of z-coordinate of this neighborhood. Points with significantly big mean distance are considered as outliers.

##### Raw point cloud of field
![alt text](https://github.com/UPOL-Plant-phenotyping-research-group/UAV-crop-analyzer/blob/main/readme_images/field.png?raw=true)

##### Point cloud of field without outliers
![alt text](https://github.com/UPOL-Plant-phenotyping-research-group/UAV-crop-analyzer/blob/main/readme_images/clean_field.png?raw=true)

As a second it's necessary to compute and remove effect of terrain trend, so experimental units are comparable. It consits of several steps. We start to identify "terrain" points with square sliding window. With given size and stride of **sliding window** we choose percentage quantile (0.01%) of lowest points as "terrain" points. Size parameter of sliding window is important parameter and has to be determined by user according to shape and size of the field. Size should be big enough, so it can't happen that in window will be only points of crop. It's recommended to define size of sliding window at least big as smaller x-y dimension of plot/experimental block.

##### Terrain points
![alt text](https://github.com/UPOL-Plant-phenotyping-research-group/UAV-crop-analyzer/blob/main/readme_images/terrain_points.png?raw=true)

Than regular terrain grid is formed with set of terrain points. For each point of grid, z-coordinate is defined as mean value of *k-nearest terrain points*. Important parameter of grid is **grid_resolution**, it determines density of points in the grid. Bigger resolution means more detailed and precise estimation of terrain.

##### Terrain grid
![alt text](https://github.com/UPOL-Plant-phenotyping-research-group/UAV-crop-analyzer/blob/main/readme_images/terrain_grid.png?raw=true)

Final step of terrain computation is fitting terrain grid points with surface spline (**NURBS** Python library) and substraction of terrain spline from field point cloud.

##### Terrain fit with B-spline
![alt text](https://github.com/UPOL-Plant-phenotyping-research-group/UAV-crop-analyzer/blob/main/readme_images/terrain_spline.png?raw=true)

##### Deterrained field
![alt text](https://github.com/UPOL-Plant-phenotyping-research-group/UAV-crop-analyzer/blob/main/readme_images/deterrained_field.png?raw=true)

##### Raw field
![alt text](https://github.com/UPOL-Plant-phenotyping-research-group/UAV-crop-analyzer/blob/main/readme_images/clean_field.png?raw=true)

### 3. Evaluation of cloud point
Next step in processing pipeline is featurization of points with **cloud_evaluator.py** module. For each point two neighborhoods are computed based on selected metric (we are using *Minkowski metric*). One neighborhood is computed with *k-nearest neighboors* method, second one with *perimeter* method. For given subset of points in both neighborhoods Principal Component Analysis is applied and eigenvalues and eigenvectors are computed. Based on computed eigenvalues and eigenvectors several features is computed (*Eigenvalues sum*, *Omnivariance*, *Eigenentropy*, *Anisotropy*, *Planarity*, *Linearity*, *Surface variation*, *Sphericity*, *Verticality*, *First order moment*, *Average distance in neighborhood*). For this step, it's convenient to use downsampling to reduce time cost. Structure of plots is computed on given subset of points. Downsampling rate should't be too small (for us 5% of points was fine). It could cause that structure of plots won't be visible anymore.

Now we have two sets of features for each point determined with different neighborhood definition. For both sets of features *Gaussian Mixture Clustering* algorithm with two components is evaluated. With this approach we are trying to find two classes of points **ground class** and **crop class**. Point is consider to be **crop class** only if it was clustered as this class for both sets of features.

##### Classified points
![alt text](https://github.com/UPOL-Plant-phenotyping-research-group/UAV-crop-analyzer/blob/main/readme_images/classification.png?raw=true)

Classification information will be used for computation of another feature of point cloud. This feature is again binary classification determining edge points in point cloud of field. Edge detection is one of the most important computational task of point cloud analysis. We developed our own approach for this task, which is based on *Support Vector Machine* algorithm. For each classified point *k-nereast neighbors neighborhood* is computed. We have **ground-crop** label (given with cluster analysis) for all points in neighborhood and this label is used as ground truth classification for fitting *Linear (plane) SVM* model. This plane has to go through analyzed point. It's expected that on the borders of plots, plane will separate space in a way that majority of **ground** points will occur under hyperplane and majority of **crop** points above hyperplane (or opposite). To evaluate difference of label between areas above and under hyperplane we define criterium **edge entropy**. This criterium is non-negative and more closer to zero it is, than point is more considered as edge point. User can determine edge points with **edge entropy criterium** values and its quantile as given percentage of points with lowest value of this criterium.

##### Example of SVM plane fit 
![alt text](https://github.com/UPOL-Plant-phenotyping-research-group/UAV-crop-analyzer/blob/main/readme_images/svm_plane.png?raw=true)

##### Edge points
![alt text](https://github.com/UPOL-Plant-phenotyping-research-group/UAV-crop-analyzer/blob/main/readme_images/edges.png?raw=true)

### 4. Plot localization
Computed features are used for plots/experimental blocks localization in the next part of pipeline, **plot_localizer.py** module. As a first points classified as **crop** are used for computation of optimal rotation of point cloud and dominant coordinate.  We are trying to find such rotation, which maximizes *z* coordinate variation for *x* and *y* axis projections. Than axis with higher variation is determined as dominant. This is important for desciption of plots orientation. In this way plot borders of rotated field will be parallel with x and y coordinates, so it can be later simply cropped with rectangles without any additional rotations. 

##### Rotated crop points
![alt text](https://github.com/UPOL-Plant-phenotyping-research-group/UAV-crop-analyzer/blob/main/readme_images/crop_rotation.png?raw=true)

Rotated **crop** points are used for localization of plot seeds. Seeds location in dominant coordinate is computed with *Fourier transform* fitting sinusoid in *z* coordinate signal aggregated with given signal span. Coordinates of sinusoid curve maximum peaks are localized plot seeds. User has to specify number of plots as one of global variables. Correct value of number of plots is important for proper plot localization, with wrong value it's not possible to fit accurate sinusoid curve.

##### Seed detection with Fourier transform
![alt text](https://github.com/UPOL-Plant-phenotyping-research-group/UAV-crop-analyzer/blob/main/readme_images/plot_signal.png?raw=true)

Our approach assumes plots in a shape of parallel rectangles. Plots borders are computed with iterative rectangle region growing algorithm. Each plot is initialized in seed and is growing until certain size. Edge points are used to stop expansion of rectangle. This step is not completely finished yet and it's last missing part.

##### Plot borders
![alt text](https://github.com/UPOL-Plant-phenotyping-research-group/UAV-crop-analyzer/blob/main/readme_images/plots.png?raw=true)

Module generates as an output batch of **las** files, each representing area of single plot.

### 5. Subplot localization
After plots localization, we have batch of plots for further analysis. In this step of processing pipeline we perform localization of subplots/experimental units in each raw (not de-terrained) plot with **subplot_detector.py** module. Again we assume that single plot is made of certain number of rectangulary shaped and parallel subplots separated with small gaps. Since field blocks are typically designed like this in field experiments, it's quite reasonable assumption. Subplot borders in not dominant coordinate is computed with *Fourier transform* fitting sinusoid in *z* coordinate signal aggregated with given signal span. Coordinates of sinusoid curve minimum peaks are localized as subplot borders. User has to specify number of plots as one of global variables. Correct value of number of subplots is important for proper subplot localization, with wrong value it's not possible to fit accurate sinusoid curve.

In our case each plot has equal number of subplots, but it is not necessary. In future we want to generalize structure of experimental blocks grid and border shape. 

![alt text](https://github.com/UPOL-Plant-phenotyping-research-group/UAV-crop-analyzer/blob/main/readme_images/subplots.png?raw=true)

To find structure of subplots *Fourier transform* is applied on raw (not de-terrained) point cloud of plot.

![alt text](https://github.com/UPOL-Plant-phenotyping-research-group/UAV-crop-analyzer/blob/main/readme_images/subplot_fourier.png?raw=true)

And with little adjusment borders of subplots can be defined.

![alt text](https://github.com/UPOL-Plant-phenotyping-research-group/UAV-crop-analyzer/blob/main/readme_images/subplot_borders.png?raw=true)

### 6. Subplot growth statistic evaluation
Last part of pipeline **field_stats.py** module evaluates growth statistic for each subplot (experimental unit/variant). It analyzes whole batch of subplots of single plot and creates structured result in **xlsx** format. For growth analysis only de-terrained points are used.

![alt text](https://github.com/UPOL-Plant-phenotyping-research-group/UAV-crop-analyzer/blob/main/readme_images/subplot.png?raw=true)

Before statistics computation, there are two preprocessing operation applied on subplot point cloud. Firstly borders of subplot are removed, this is defined by user with percentage value for *dominant* and *not dominant* coordinate. Next action is to remove points, which has low value of *z*-coordinate. These points are not considered as **crop** points and are filtered out with quantile ot threshold value.

![alt text](https://github.com/UPOL-Plant-phenotyping-research-group/UAV-crop-analyzer/blob/main/readme_images/cleaned_subplot.png?raw=true)

Our growth statistics is volume of subplot biomass in preprocessed subplot area. To compute volume we need to compute crop surface. We define x-y regular grid for subplot and *z*-coordinate of each point in the grid is defined as *z* coordinate mean value of *k-nearest neighboors* of subplot point cloud. Than B-Spline is fitted in terrain grid points with **NURBS** Python library.

![alt text](https://github.com/UPOL-Plant-phenotyping-research-group/UAV-crop-analyzer/blob/main/readme_images/crop_surface.png?raw=true)

Volume is computed as sum of blocks defined with area given by square sized sliding window in x-y hyperplane and height of each block as median of B-spline value of points localized in given area/sliding window.

## TO DO / IMPROVEMENTS 

-   Software computation acceleration: Numba, GPU, Concurent programming, definiton of new arrays with predefined dimensions (not arbitrary)
-   local point density paremeter used in neghborhood computations
-   better understanding of feature selection
-   not just rectangular shapes or grid shapes of fields -> contour detection
-   improvement of subplot localization algorithm


## INSTALLATION

### Prerequisities
1. As a first install Python up to date version (not older than **3.9.X**) on your server. Follow instructions [of this website] (https://realpython.com/installing-python) to install python required version.
3. Python virtualenv package is required. Open terminal and execute `python3 -m pip install virtualenv` (for Unix) or `py -m pip install --user virtualenv` (for Windows) command to install this package.

### Configure local environment
Create your own local environment, for more see [guide](https://pipa.io/en/latest/user_guide/), and install dependencies requirements.txt contains list of packages and can be installed as

```
Michals-MacBook-Pro:Repos michal$ cd UAV-crop-analyzer/ 
Michals-MacBook-Pro:UAV-crop-analyzer michal$ `python -m venv UAV`
Michals-MacBook-Pro:UAV-crop-analyzer michal$ source UAV/bin/activate  
Michals-MacBook-Pro:UAV-crop-analyzer michal$ pip install -r requirements.txt
Michals-MacBook-Pro:UAV-crop-analyzer michal$ deactivate  
```

## Use

### Activalte local virtual environment

```
Michals-MacBook-Pro:Repos michal$ cd UAV-crop-analyzer/ 
Michals-MacBook-Pro:UAV-crop-analyzer michal$ source UAV/bin/activate  
```

### Configure global variables
In configs folder edit with text editor file **config_global.py** and configure global variablles:
```
Parameter LASFILE_PATH navigates software in folder, where target las file is
stored and where output files of this module will be generated.
```

```
Parameter FILENAME determines name of processed las file.
```

```
Parameter PLOT_NUM is number of experimental blocks in field.
```

```
Parameter SUBPLOT_NUM is number of experimental units in single experimental block.
```


### Manual field localizer
To manually localize field/region of interest in raw point cloud, use **manual_field_localizer.py** module.

1. Call module from terminal: ```(UAV) Michals-MacBook-Pro:UAV-crop-analyzer michal$ python manual_field_localizer.py```
2. Find x-y coordinates of rectangular field with visualization tool and in created file **field metadata.json** modify borders of ractangle.
3. Run module again to visually check field borders: ```(UAV) Michals-MacBook-Pro:UAV-crop-analyzer michal$ python manual_field_localizer.py```


### Terrain handler
To remove outlier and de-terrain point cloud of field, use **terrain_handler.py** module. 

1. In configs folder edit with text editor file **config_terrain_handler.py** and configure module parameters (we are going to mention just important parameters):

```
**terrain_evaluator_Parameters**

Parameter DOWNSAMPLING_RATE determines percentage number of downsampled points of raw points
which will be processed with module. Since point clouds are huge files in general, to use 
subset of points can significantly accelerate computation and decrease processing time.
```

```
**outlier_detector_Parameters**

Parameter DEVIANCE is essential for outlier detection. For each point average euclidean distance of z-coordinate in its 
perimeter neighborhood is computed. We got sample of average euclidean distance of z-coordinate and we compute mean and standard
deviation of the sample. DEVIANCE parameter defines how many standard deviations higher than sample mean has to be single distance
of sample, to be considere as outlier.
```

```
**terrain_filter_Parameters**

Parameter WINDOW_SIZE defines size (in meters) of square sliding window (i x-y hyperplane), which used
for terrain points selection in given area of window. It's important to define the WINDOW_SIZE big enough,
so terrain pointswill be always in the window area. It should not happen that filtered terrain points in
window area will include points of crop. Recommendation is to choose WINDOW_SIZE bigger than smaller
dimension (in x-y hyperplane) of plots in your experiment.
```

```
**terrain_filter_Parameters**

Parameter WINDOW_STRIDE defines how is sliding window moved over analyzed area. Sliding windows starts in
origin of coordinates and is moved in x and y coordinate direction with given step (in meters). This step
is WINDOW_STRIDE.
```

```
**terrain_grid_Parameters**

Parameter GRID_RESOLUTION defines point density of terrain grid. GRID_RESOLUTION is number of equidistantly
distributed points in x axis range and the same number of points is euqidistantly distributed in y axis range.
In total gird is formed with GRID_RESOLUTION x GRID_RESOLUTION points 
```

2. Call module from terminal: ```(UAV) Michals-MacBook-Pro:UAV-crop-analyzer michal$ python terrain_handler.py```

### Cloud evaluator
To evaluate features of de-terrain field point cloud, use **cloud_evaluator.py** module. 

1. In configs folder edit with text editor file **config_cloud_evaluator.py** and configure module parameters (we are going to mention just important parameters):

```
**cloud_evaluator_Parameters**

Parameter DOWNSAMPLING_RATE determines percentage number of downsampled points of raw points
which will be processed with module. Since point clouds are huge files in general, to use 
subset of points can significantly accelerate computation and decrease processing time.
```

```
**cloud_featurizer_Parameters**

Parameter RADIUS defines neighborhood points of analyzed point for perimeter neighborhood method. 
Evaluation of features for analyzed point is given with these points.
```

```
**cloud_featurizer_Parameters**

Parameter K defines neighborhood points of analyzed point for k-nearest neighbors neighborhood method.
Evaluation of features for analyzed point is given with these points.
```

```
**edge_detector_Parameters**

Parameter K defines fixed number of closest points to analyzed point, which are used for
computation of edge_entropy criterium for given point.
```

```
**edge_detector_Parameters**

Parameter ENTROPY_QUANTILE defines percentage of points with smallest edge_entropy criterium.
These points are considered as edge points.
```

2. Call module from terminal: ```(UAV) Michals-MacBook-Pro:UAV-crop-analyzer michal$ python cloud_evaluator.py```
  
### Plot localizer
To localize plots/experimental blocks in field point cloud, use **plot_localizer.py** module. 

1. In configs folder edit with text editor file **config_plot_localizer.py** and configure module parameters (we are going to mention just important parameters):

```
**plot_detector_Parameters**

Parameter SIGNAL_SPAN defines size of step (in meters) for x and y axis, which is used for z-coordinate
signal computation. Value of z-coordinate of points localized in the range is used to compute some statistic 
(sum, mean, etz.). Smaller SIGNAL_SPAN parameter is more detail we are able detect, but computation time grows.
Big SIGNAL_SPAN values are not recommended, it can cause loss of structure in computed signal.
``` 

2. Call module from terminal: ```(UAV) Michals-MacBook-Pro:UAV-crop-analyzer michal$ python plot_localizer.py```


### Subplot localizer
To localize subplots/experimental units in plot point cloud, use **subplot_localizer.py** module. 

1. In configs folder edit with text editor file **config_subplot_localizer.py** and configure module parameters (we are going to mention just important parameters):

```
**subplot_detector_Parameters**

Parameter SIGNAL_SPAN defines size of step (in meters) for not determinative axis, which is used for z-coordinate
signal computation to detect subplots borders. Value of z-coordinate of points localized in the range is used
to compute some statistic (sum, mean, etz.). Smaller SIGNAL_SPAN parameter is more detail we are able detect, 
but computation time grows. Big SIGNAL_SPAN values are not recommended, it can cause loss of structure in computed signal.
```

2. Call module from terminal: ```(UAV) Michals-MacBook-Pro:UAV-crop-analyzer michal$ python subplot_localizer.py```

### Plot stats evaluator
To evaluate growth statistics for all subplots in given plot point cloud (it's possible to evaluate batch of plots), use **plot_stat_evaluator.py** module.

1. In configs folder edit with text editor file **config_plot_stat_evaluator.py** and configure module parameters (we are going to mention just important parameters):

```
**cut_border_Parameters**

Parameter MAJOR_BORDER_PCT determines percentage part which is removed from size of determinative coordinate.
It means that half of MAJOR_BORDER_PCT value is removed from lower and half from upper part of subplot. The 
reason is to remove noisy borders of subplot.
```

```
**cut_border_Parameters**

Parameter MINOR_BORDER_PCT determines percentage part which is removed from size of not determinative coordinate.
It means that half of MINOR_BORDER_PCT value is removed from lower and half from upper part of subplot. The 
reason is to remove noisy borders of subplot.
```

```
**class point_filter_Parameters**

Parameter METHOD determines the way how are points with low z-coordinate value cleaned oout from subplot point cloud.
Quantile method filters out given percentage of lowest points. Threshold method filters out points up to certain level
of z-coordinate value.
```

```
**class point_filter_Parameters**

Parameter HEIGHT_QUANTILE filters out from subplot point cloud given percentage of points with lowest value
of z-coordinate.
```

```
**class point_filter_Parameters**

Parameter HEIGHT_THRESHOLD filters out from subplot point cloud points with value of z-coordinate lower than
HEIGHT_THRESHOLD value.
```

```
**terrain_grid_Parameters**

Parameter K defines fixed number of closest terrain points to given grid point, which are used for
computation computation of grid point z-coordinate value as mean value of z-coordinate of k-closest
terrain points.
```

```
**terrain_grid_Parameters**

Parameter GRID_RESOLUTION defines point density of terrain grid. GRID_RESOLUTION is number of equidistantly
distributed points in x axis range and the same number of points is euqidistantly distributed in y axis range.
In total gird is formed with GRID_RESOLUTION x GRID_RESOLUTION points.
```
            
```
**volume_evaluator_Parameters**

Parameter AREA_SIZE defines size of squared sliding window, which is sliding around subplot area and is used for
volume computation in this small area of sliding window. The principle of subplot volume computation is the same as
as integration. The volume is sum of volumes calculated in all sliding window areas in subplot area
```

```
**volume_evaluator_Parameters**

Parameter METHOD determines the way, how volume is computed in area of sliding window. Raw method computes height 
of block as median of z-coordinate. Surface method uses B-Spline fitted on the surface of subplot. Height of block
given by sliding window is calculated as median of B-Spline values in given area.
```
 
2. Call module from terminal: ```(UAV) Michals-MacBook-Pro:UAV-crop-analyzer michal$ python plot_stat_evaluator.py```
