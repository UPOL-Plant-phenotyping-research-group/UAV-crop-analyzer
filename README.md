# UAV-crop-analyzer

## Authors
Michal Polak [1]

[1] Palacky Univ, Fac Sci, Laboratory of Growth Regulators, Olomouc 77900, Czech Republic

## Introduction

UAV-crop-analyzer is a tool developed for purpose of growth analysis of various crops based on its height. This is a first version/prototype of software, which was developed in Python 3.9 programming language. Expected input for analyzer is point cloud in **las** format. Software was prototyped with data generated with **Ricopter** UAV machine manufactured by **Riegl** enterprise. (Tady by se chtelo povenovat popisu Coordinate system, na jakem merime). Since we didn't produce sufficient timelines measurement of our fields, software is designed to analyse static point cloud of field at this moment. In future we plan develop more complex analysis, processing whole batch of time-sorted point clouds of field. Crucial *Analyzer* assumption is that crop is growing in regular rectangular grid of plots and subplots (this structure will be explained more precisely later). *Analyzer* is composed of 6 independent modules and its goal is to compute growth statistics about subplots (experimental units), which represents crop variants in experiment. Advantage of software is that algorithms used in *Analyzer* are unsupervised and it's use is semi-automated. Each module have several parameters configurable by user, which effects final output of module. The goal is to reduce the number of configurable parameters as much as possible.


## Modules

Neighborhoods described in next sections are based on x-y axis.

### 1. Manual localization of Field/ROI
In first step user will use module **manual_field_crop.py**. This module visualizes raw point cloud (with given downsampling rate) and generates **field_metadata.json** file. In **field_metadata.json** file user will define x-y coordinates of ROI (region of interest). User should define ROI in a way to define ROI as small as possible, so unnecessary noisy points are excluded.

![alt text](https://github.com/UPOL-Plant-phenotyping-research-group/UAV-crop-analyzer/blob/main/readme_images/ROI.png?raw=true)

### 2. Field preprocessing
In next part of pipeline, user will call **terrain_handler.py** module. This module performs two essential preprocessing steps *Outliers removal* and *Terrain effect removal* and prepares point cloud of field for further analysis.

As a first outliers are detected and removed from point cloud. For each point is computed local neigborhood (radius or k-nearest neighbors) and mean distance of z-coordinate of this neighborhood. Points with significantly (deviance is configurable) big mean distance are considered as outliers.

##### Raw point cloud of field
![alt text](https://github.com/UPOL-Plant-phenotyping-research-group/UAV-crop-analyzer/blob/main/readme_images/field.png?raw=true)

##### Point cloud of field without outliers
![alt text](https://github.com/UPOL-Plant-phenotyping-research-group/UAV-crop-analyzer/blob/main/readme_images/clean_field.png?raw=true)

As a second it's necessary to compute and remove effect of terrain trend, so experimental units are comparable. It consits of several steps. We start to identify "ground" points with square sliding window. With given size and stride of sliding window we choose 0.01% of lowest points as "ground" points. Size parameter of sliding window is important parameter and has to be determined by user according to shape of the field. Size should be big enough, soit can't happen that in window will be only points of crop. It's recommended to define size of sliding window at least big as smaller x-y dimension of plot.

##### Terrain points
![alt text](https://github.com/UPOL-Plant-phenotyping-research-group/UAV-crop-analyzer/blob/main/readme_images/terrain_points.png?raw=true)

Than regular terrain grid is formed with set of terrain points. For each point of grid, z-coordinate is defined as mean value of k-nearest terrain points. Important parameter of grid is *resolution*, it determines density of points in the grid. Bigger resolution means more detailed and precise estimation of terrain.

##### Terrain grid
![alt text](https://github.com/UPOL-Plant-phenotyping-research-group/UAV-crop-analyzer/blob/main/readme_images/terrain_points.png?raw=true)

Final step of terrain computation is fitting terrain grid points with surface spline with **NURBS** Python library and substract spline of terrain from field point cloud.

##### Terrain fit with B-spline
![alt text](https://github.com/UPOL-Plant-phenotyping-research-group/UAV-crop-analyzer/blob/main/readme_images/terrain_spline.png?raw=true)

##### Deterrained field
![alt text](https://github.com/UPOL-Plant-phenotyping-research-group/UAV-crop-analyzer/blob/main/readme_images/deterrained_field.png?raw=true)

##### Raw field
![alt text](https://github.com/UPOL-Plant-phenotyping-research-group/UAV-crop-analyzer/blob/main/readme_images/clean_field.png?raw=true)

### 3. Evaluation of cloud point
Next step in processing pipeline is featurization of points. For each point two neighborhoods are computed based on selected metric (we are using Minkowski metric). One neighborhood is computed with k-nearest neighboors method, second one with radius method. For given subset of points in both neighborhoods Principal Component Analysis is applied and eigenvalues and eigenvectors are computed. Based on computed eigenvalues and eigenvectors several features is computed (*Eigenvalues sum*, *Omnivariance*, *Eigenentropy*, *Anisotropy*, *Planarity*, *Linearity*, *Surface variation*, *Sphericity*, *Verticality*, *First order moment*, *Average distance in neighborhood*). In this step it's convenient to use downsampling to reduce time cost. Structure of plots is computed on given subset of points. Downsampling rate should't be so small (for us 5% of points was fine), that structure of plots won't be visible anymore.

Now we have two sets of features for each point determined with different neighborhood definition. For both sets of features Gaussian Mixture Clustering algorithm with two components is evaluated. With this approach we are trying to find two classes of points **ground class** and **crop class**. Point is consider to be **crop class** only if it was clustered as this class for both sets of features.

##### Classified points
![alt text](https://github.com/UPOL-Plant-phenotyping-research-group/UAV-crop-analyzer/blob/main/readme_images/classification.png?raw=true)





- improvements:
-   Software computation acceleration: Numba, GPU, Concurent programming, definiton of new arrays with predefined dimensions (not arbitrary)
-   local point density paremeter used in neghborhood computations
-   better understanding of feature selection
-   not just rectangular shapes or grid shapes of fields

