# UAV-crop-analyzer

## Authors
Michal Polak [1]

[1] Palacky Univ, Fac Sci, Laboratory of Growth Regulators, Olomouc 77900, Czech Republic

## Introduction

UAV-crop-analyzer is a tool developed for purpose of growth analysis of various crops based on its height. This is a first version/prototype of software, which was developed in Python 3.9 programming language. Expected input for analyzer is point cloud in **las** format. Software was prototyped with data generated with **Ricopter** UAV machine manufactured by **Riegl** enterprise. (Tady by se chtelo povenovat popisu Coordinate system, na jakem merime). Since we didn't produce sufficient timelines measurement of our fields, software is designed to analyse static point cloud of field at this moment. In future we plan develop more complex analysis, processing whole batch of time-sorted point clouds of field. Crucial **UAV-crop-analyzer** assumption is that crop is growing in regular rectangular grid of plots and subplots (this structure will be explained more precisely later). **UAV-crop-analyzer** is composed of 6 independent modules and its goal is to compute growth statistics of subplots (experimental units), which represents crop variants in experiment. Advantage of software is that algorithms used in **UAV-crop-analyzer** are *unsupervised* and it's use is *semi-automated*. Each module have several parameters configurable by user, which effects final output of module. The goal is to reduce the number of configurable parameters as much as possible.


## Modules

Neighborhoods described in next sections are based on x-y axis.

### 1. Manual localization of Field/ROI
In first step user will use module **manual_field_crop.py**. This module visualizes raw point cloud (with given downsampling rate) and generates **field_metadata.json** file. In **field_metadata.json** file user will define x-y coordinates of ROI (region of interest). User should define ROI in a way to define ROI as small as possible, so unnecessary noisy points are excluded.

![alt text](https://github.com/UPOL-Plant-phenotyping-research-group/UAV-crop-analyzer/blob/main/readme_images/ROI.png?raw=true)

### 2. Field preprocessing
In next part of pipeline, user will call **terrain_handler.py** module. This module performs two essential preprocessing steps Outliers removal and Terrain effect removal and prepares point cloud of field for further analysis.

As a first outliers are detected and removed from point cloud. For each point is computed local neigborhood (*radius* or *k-nearest neighbors*) and mean distance of z-coordinate of this neighborhood. Points with significantly (deviance is configurable) big mean distance are considered as outliers.

##### Raw point cloud of field
![alt text](https://github.com/UPOL-Plant-phenotyping-research-group/UAV-crop-analyzer/blob/main/readme_images/field.png?raw=true)

##### Point cloud of field without outliers
![alt text](https://github.com/UPOL-Plant-phenotyping-research-group/UAV-crop-analyzer/blob/main/readme_images/clean_field.png?raw=true)

As a second it's necessary to compute and remove effect of terrain trend, so experimental units are comparable. It consits of several steps. We start to identify "terrain" points with square sliding window. With given size and stride of **sliding window** we choose 0.01% of lowest points as "terrain" points. Size parameter of sliding window is important parameter and has to be determined by user according to shape of the field. Size should be big enough, soit can't happen that in window will be only points of crop. It's recommended to define size of sliding window at least big as smaller x-y dimension of plot.

##### Terrain points
![alt text](https://github.com/UPOL-Plant-phenotyping-research-group/UAV-crop-analyzer/blob/main/readme_images/terrain_points.png?raw=true)

Than regular terrain grid is formed with set of terrain points. For each point of grid, z-coordinate is defined as mean value of *k-nearest terrain points*. Important parameter of grid is **resolution**, it determines density of points in the grid. Bigger resolution means more detailed and precise estimation of terrain.

##### Terrain grid
![alt text](https://github.com/UPOL-Plant-phenotyping-research-group/UAV-crop-analyzer/blob/main/readme_images/terrain_grid.png?raw=true)

Final step of terrain computation is fitting terrain grid points with surface spline of **NURBS** Python library and substraction of terrain spline from field point cloud.

##### Terrain fit with B-spline
![alt text](https://github.com/UPOL-Plant-phenotyping-research-group/UAV-crop-analyzer/blob/main/readme_images/terrain_spline.png?raw=true)

##### Deterrained field
![alt text](https://github.com/UPOL-Plant-phenotyping-research-group/UAV-crop-analyzer/blob/main/readme_images/deterrained_field.png?raw=true)

##### Raw field
![alt text](https://github.com/UPOL-Plant-phenotyping-research-group/UAV-crop-analyzer/blob/main/readme_images/clean_field.png?raw=true)

### 3. Evaluation of cloud point
Next step in processing pipeline is featurization of points. For each point two neighborhoods are computed based on selected metric (we are using *Minkowski metric*). One neighborhood is computed with *k-nearest neighboors* method, second one with *radius* method. For given subset of points in both neighborhoods Principal Component Analysis is applied and eigenvalues and eigenvectors are computed. Based on computed eigenvalues and eigenvectors several features is computed (*Eigenvalues sum*, *Omnivariance*, *Eigenentropy*, *Anisotropy*, *Planarity*, *Linearity*, *Surface variation*, *Sphericity*, *Verticality*, *First order moment*, *Average distance in neighborhood*). In this step it's convenient to use downsampling to reduce time cost. Structure of plots is computed on given subset of points. Downsampling rate should't be too small (for us 5% of points was fine). It could cuse that structure of plots won't be visible anymore.

Now we have two sets of features for each point determined with different neighborhood definition. For both sets of features *Gaussian Mixture Clustering* algorithm with two components is evaluated. With this approach we are trying to find two classes of points **ground class** and **crop class**. Point is consider to be **crop class** only if it was clustered as this class for both sets of features.

##### Classified points
![alt text](https://github.com/UPOL-Plant-phenotyping-research-group/UAV-crop-analyzer/blob/main/readme_images/classification.png?raw=true)

Classification information will be used for computation of another feature of point cloud. This feature is again binary classification determining edge points of plots. Edge detection is one of the most important computational task of point clouds analysis. We developed our own approach for this task, which is based on *Support Vector Machine* algorithm. For each classified point *k-nereast neighbors neighborhood* is computed. We have **ground-crop** label for all points in neighborhood and this label is used as ground truth classification for fitting *Linear (plane) SVM* model. This plane has to go through analyzed point. It's expected that on the borders of plots, plane will separate space in a way that majority of **ground** points will on one side of plane and majority of **crop** points on the other side. For this purpose we define criterium **edge entropy**. This criterium is non-negative and closer to zero it is, than point could be more considered as edge point. User can determine edge points with **edge entropy** criterium values and its quantile. Like this software provides subset of points with lowest value of **edge entropy** given with quantile.

##### Example of SVM plane fit 
![alt text](https://github.com/UPOL-Plant-phenotyping-research-group/UAV-crop-analyzer/blob/main/readme_images/svm_plane.png?raw=true)

##### Edge points
![alt text](https://github.com/UPOL-Plant-phenotyping-research-group/UAV-crop-analyzer/blob/main/readme_images/edges.png?raw=true)

### 4. Plot localization
Computed features will be used for plots localization in the next part of pipeline. As a first points classified as **crop** are used for computation of optimal rotation of point cloud and dominant coordinate.  We are trying to find such rotation, which maximizes sum of *x* and *y* coordinates variation of *z* coordinate. Than coordinate with higher variation is determined as dominant. This is important for desciption of plots orientation.

##### Rotated crop points
![alt text](https://github.com/UPOL-Plant-phenotyping-research-group/UAV-crop-analyzer/blob/main/readme_images/crop_rotation.png?raw=true)

Rotated **crop** points are used for localization of plot seeds. Seeds are computed with *Fourier transform* approach and are **crop** points with strongest signal of z-coordinate. User has to specify number of plots.

##### Seed detection with Fourier transform
![alt text](https://github.com/UPOL-Plant-phenotyping-research-group/UAV-crop-analyzer/blob/main/readme_images/plot_signal.png?raw=true)

Our approach assumes plots in a shape of parallel rectangles. Plots borders are computed with iterative rectangle region growing algorithm. Each plot is initialized in seed and is growing until certain size. Edge points are used to stop expansion of rectangle. This step is not completely finished yet and it's last missing part.

##### Plot borders
![alt text](https://github.com/UPOL-Plant-phenotyping-research-group/UAV-crop-analyzer/blob/main/readme_images/plots.png?raw=true)

Module generates as an output batch of **las** files, each representing area of single plot.

### 5. Subplot localization
After plots are localized, we have batch of plots for further analysis. In this step of processing pipeline we describe localization of subplots, which is the same for each plot. Again we assume that single plot is made up of certain number of rectangular shaped and parallel subplots separated with small gaps. Since field blocks are designed like this, it's quite reasonable assumption. In our case each plot has equal number of subplots, but it is not necessary. In future we want to generalize structure of plot and subplot grid. 

![alt text](https://github.com/UPOL-Plant-phenotyping-research-group/UAV-crop-analyzer/blob/main/readme_images/subplots.png?raw=true)

To find structure of subplots *Fourier transform* is applied on raw (not de-terrained) point cloud of plot.

![alt text](https://github.com/UPOL-Plant-phenotyping-research-group/UAV-crop-analyzer/blob/main/readme_images/subplot_fourier.png?raw=true)

And with little adjusment borders of subplots can be defined.

![alt text](https://github.com/UPOL-Plant-phenotyping-research-group/UAV-crop-analyzer/blob/main/readme_images/subplot_borders.png?raw=true)

### 6. Subplot growth statistic evaluation
Last part of pipeline evaluates growth statistic for each subplot (experimental unit/variant). It analyzes whole batch of subplots of single plot and creates structured result in **xlsx** format. For growth analysis only de-terrained points  are used.

![alt text](https://github.com/UPOL-Plant-phenotyping-research-group/UAV-crop-analyzer/blob/main/readme_images/subplot.png?raw=true)

Before statistics computation, there are two preprocessing operation applied on subplot point cloud. Firstly borders of subplot are removed, this is defined by user with percentage value for *x* and *y* coordinate. Next action is to remove points, which has low value of *z*-coordinate. These points are not considered as **crop** points and are filtered out with quantile value.

![alt text](https://github.com/UPOL-Plant-phenotyping-research-group/UAV-crop-analyzer/blob/main/readme_images/cleaned_subplot.png?raw=true)

Our growth statistics is volume of subplot biomass. To compute volume we need to compute crop surface. We define regular grid for subplot and *z*-coordinate of each point in the grid is defined as mean value of *k-nearest neighboors* of subplot point cloud. Than B-Spline is fited in terrain grid points with **NURBS** Python library.

![alt text](https://github.com/UPOL-Plant-phenotyping-research-group/UAV-crop-analyzer/blob/main/readme_images/crop_surface.png?raw=true)

Volume is computed as Lebesgue integral with square sized sliding window. Height of each area defined with sliding window is median *z*-coordinate value given with all points localize in given area.

## TO DO / IMPROVEMENTS 

-   Software computation acceleration: Numba, GPU, Concurent programming, definiton of new arrays with predefined dimensions (not arbitrary)
-   local point density paremeter used in neghborhood computations
-   better understanding of feature selection
-   not just rectangular shapes or grid shapes of fields -> contour detection
-   improvement of subplot localization algorithm

