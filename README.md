# UAV-crop-analyzer

## Authors
Michal Polak [1]

[1] Palacky Univ, Fac Sci, Laboratory of Growth Regulators, Olomouc 77900, Czech Republic

## Introduction

UAV-crop-analyzer is a tool developed for purpose of growth analysis of various crops based on its height. This is a first version/prototype of software, which was developed in Python 3.9 programming language. Expected input for analyzer is point cloud in **las** format. Software was prototyped with data generated with **Ricopter** UAV machine manufactured by **Riegl** enterprise. (Tady by se chtelo povenovat popisu Coordinate system, na jakem merime). Since we didn't produce sufficient data timelines of our fields, software is designed to analyse static point cloud of field at this moment. In future we plan develop more complex analysis, processing whole batch of time-sorted point clouds of field. Crucial *Analyzer* assumption is that crop is growing in regular rectangular grid of plots and subplots (this structure will be explained more precisely later). *Analyzer* is composed





## Modules




- improvements:
-   Numba, GPU, Concurent programming
-   point density paremeter
-   not just rectangular shapes or grid shapes of fields
