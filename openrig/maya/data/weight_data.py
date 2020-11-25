'''
This is going to work on Maya sets in the scene.
'''
from collections import OrderedDict
import maya.cmds as mc
import openrig.maya.data.maya_data as maya_data
import openrig.maya.weights as weights
import openrig.maya.weightObject as weightObject
import openrig.maya.transform as tansform
import openrig.shared.common as common
import numpy
import getpass
from time import gmtime, strftime
import json
import os

class WeightData(maya_data.MayaData):
    '''
    This class is created to store and apply data for Maya sets.
    '''
    def __init__(self):
        '''
        The constructor for the sets class.
        '''
        super(WeightData, self).__init__()

    def gatherData(self, node, geometry=None):
        '''
        This will gather the data for a given deformer. If the geometry argument is used, then we will only
        get the data for that geometry

        :param node: The deformer you wish to gather data for.
        :type node: str
        :param geometry: The geometry you want to gather deformer information for.
        :type geometry: str
        '''
        super(WeightData, self).gatherData(node)

        weight_object = weights.getWeights(node, geometry=geometry)
        data = OrderedDict()
        # get the geometry
        if geometry:
            if not mc.objExists(geometry):
                raise RuntimeError("{} doesn't exists in the current Maya session!".format(geometry))
            # make sure we have the shape of the geometry for all deformers except the skinCluster
            geoDagPath = tansform.getDagPath(geometry)
            geoDagPath.extendToShape()
            geometryFullPath = geoDagPath.fullPathName()
        else:
            # get the geometry and the iterator to use for looping through the mesh points for wts.
            geometry = mc.deformer(node, q=True, g=True)[0]
            geoDagPath = tansform.getDagPath(geometry)
            geoDagPath.extendToShape()

        data['shape'] = geoDagPath.partialPathName()
        data['maps'] = weight_object.getMaps() or ['envelope']
        data['weights'] = numpy.array(weight_object.getWeights()).tolist()#[list(wts) for wts in ]
        self._data[node].update(data)


    def read(self, filepath):
        '''
        This is overloading the default bahavior of load since we need to convert data after we load it.

        :param filepath: The path to the file you're trying to load
        :type filepath: str
        '''
        super(WeightData, self).read(filepath)

        for node in self._data:
            self._data[node]['weights'] = weightObject.WeightObject(weights=self._data[node]['weights']).getWeights()

    def write(self, filepath, createDirectory=True):
        '''
        This will write a dictionary of information out to disc in .json format.

        :param data: This is the dictionary of info you want to write out.
        :type data: dict | orderedDict

        :param filepath: The path to the file you wish to write.
        '''
        if not isinstance(self._data, (dict, OrderedDict)):
            raise TypeError("The data must be passed in as a dictionary.")
        # writeData is user specific just on export
        writeData = OrderedDict(user=getpass.getuser(),
                                type= self.__class__.__name__,
                                time=strftime("%Y-%m-%d %H:%M:%S", gmtime()))
        writeData['data'] = self._data
        # dump data to json format and write it out to disk.
        data = json.dumps(writeData)

        # Create directory if needed
        directory = os.path.dirname(filepath)
        if createDirectory:
            if not os.path.isdir(directory):
                print('making directory', directory)
                os.makedirs(directory, 755)

        # Write
        f = open(filepath, 'w')
        f.write(data)
        f.close()

        # set a new filepath on the class.
        self._filepath = filepath

    def applyData(self, nodes):
        '''
        Applies the data for the given nodes.

        :param nodes: Array of sets you want to apply the data to.
        :type nodes: list | tuple
        '''
        nodes = common.toList(nodes)
        # loop through the nodes and apply the data.
        for node in nodes:
            # check to make sure the node we're looking for exist in the data
            if self._data.has_key(node):
                map_list = [map for map in self._data[node]['maps'] if map !='envelope']
                weight_object = weightObject.WeightObject(maps=map_list, weights=self._data[node]['weights'])
                weights.setWeights(node, weights=weight_object, geometry=self._data[node]['shape'])