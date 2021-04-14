from featurizer import CloudFeaturizer
from classifier import VegetationClassifier
from edge_detection import EdgeDetector
import numpy as np
from laspy.file import File
import random
from utils import save_img
import os


class CloudEvaluator(object):

    def __init__(self, lasFile_path: str, filename: str, downsampling_rate = 1):

        self.path = lasFile_path
        self.filename = filename
        self.dw_rate = downsampling_rate
        self.lasFile = File(self.path + self.filename, mode='r')
        self.points = np.vstack((self.lasFile.x - self.lasFile.header.min[0],self.lasFile.y - self.lasFile.header.min[1],self.lasFile.z - self.lasFile.header.min[2])).transpose()
        self.point_cloud = self.points[random.sample(range(0,self.points.shape[0]), round(self.points.shape[0]*self.dw_rate)),:]

    def _execute(self):

        if not os.path.exists(self.path + 'field_evaluation/'): os.makedirs(self.path + 'field_evaluation/')

        print('EVALUATION OF POINT CLOUD STARTED')

        #Initialize CloudFeaturizer class
        featurizer = CloudFeaturizer(self.point_cloud, 'minkowski', [0,1])
        print('POINT FEATURIZATION')
        #Compute features
        features = featurizer.collect_cloud_features()
        fkeys = list(features.keys())
        print('POINT CLASSIFICATION')
        #Initialize VegetationClassifier class
        classifier = VegetationClassifier(self.point_cloud, features)
        #Compute classification
        crop_label, valid_idx = classifier.classify_vegetation()
        #sample valid (classified) points for further analysis
        classified_points = self.point_cloud[valid_idx,:]
        #Visualize na save classification result
        save_img(np.hstack((classified_points, crop_label.reshape(-1,1))), 'classification', self.path + 'field_evaluation/', 90, 0)
        print('EDGE DETECTION')
        #Initialize EdgeDetector class
        detector = EdgeDetector(classified_points, crop_label, 0.03, 50)
        edge_label = detector.get_edge_points()
        save_img(np.hstack((classified_points, edge_label.reshape(-1,1))), 'edge', self.path + 'field_evaluation/', 90, 0)

        coords = classified_points
        coords[:,0] = coords[:,0] + self.lasFile.header.min[0]
        coords[:,1] = coords[:,1] + self.lasFile.header.min[1]
        coords[:,2] = coords[:,2] + self.lasFile.header.min[2]

        np.savetxt(self.path + 'field_evaluation/' + '{}_features.csv'.format(fkeys[0]), features[fkeys[0]])
        np.savetxt(self.path + 'field_evaluation/' + '{}_features.csv'.format(fkeys[1]), features[fkeys[1]])
        np.savetxt(self.path + 'field_evaluation/' + 'labels.csv', np.hstack((coords, crop_label.reshape(-1,1), edge_label.reshape(-1,1))), delimiter=",")
        
        print('EVALUATION OF POINT CLOUD FINISHED')
        
if __name__ == '__main__':

    CE = CloudEvaluator('/Users/michal/Desktop/Dev/Data/Lidar/20/', 'deterrained_points.las', 0.05)
    CE._execute()