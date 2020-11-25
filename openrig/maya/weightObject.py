'''
This module will have the class that deals with weights.
'''
import numpy
from showtools.maya import common
class WeightObject(object):
    '''
    Class that contains maps and weights per map.
    '''
    def __init__(self, maps=list(), weights=list()):
        '''
        This is the constructor for our weightObject

        :param maps: List of maps that will have a corresponding weights array per component
        :type maps: list

        :param weights: List of numpy array's storing influnce value per component
        :type weights: list
        '''
        super(WeightObject, self).__init__()

        self.__maps = list()
        self.__weights = list()
        self.setMaps(maps)
        self.setWeights(weights)
        self._index = 0
        
    def __iter__(self):
        return self

    def __add__(self, other):
        '''
        This will add two weight objects together and return a new one
        :param other: another weight object
        :return: WeightObject
        '''
        if not isinstance(other, WeightObject):
            raise TypeError('{} is not a weight object. Must pass a WeightObject as type.'.format(other))
        other_map_list = other.getMaps()
        other_weight_list = other.getWeights()
        new_weight_list = list()
        new_map_list = list()

        if other_map_list:
            for other_map in other_map_list:
                if other_map in self.__maps:
                    new_map_list.append(other_map)
                    new_weights = self.__weights[self.__maps.index(other_map)] + other_weight_list[
                        other_map_list.index(other_map)]
                    new_weight_list.append(new_weights)
        else:
            new_weight_list.append(self.__weights[0] + other_weight_list[0])
        return WeightObject(new_map_list, new_weight_list)

    def __sub__(self, other):
        '''
        This will subtract one weight object from another and return a new one
        :param other: The other weightObject
        :return: subtracted weightObject
        '''
        if not isinstance(other, WeightObject):
            raise TypeError('{} is not a weight object. Must pass a WeightObject as type.'.format(other))
        #
        other_map_list = other.getMaps()
        other_weight_list = other.getWeights()
        new_weight_list = list()
        new_map_list = list()

        if other_map_list:
            for other_map in other_map_list:
                if other_map in self.__maps:
                    new_map_list.append(other_map)
                    new_weights = self.__weights[self.__maps.index(other_map)] - other_weight_list[
                        other_map_list.index(other_map)]
                    new_weight_list.append(new_weights)
        else:
            new_weight_list.append(self.__weights[0] - other_weight_list[0])
        return WeightObject(new_map_list, new_weight_list)

    def __getitem__(self, key):
        '''
        This will return the map and weight at the given key
        :param map:
        :return:
        '''
        map = ''
        weights = numpy.array()
        if not self.__maps:
            map = ''
            weights = numpy.array(self.__weights[0])
        elif isintance(key, int):
            map = str(self.__maps[key])
            weights = numpy.array(self.__weights[key])
        elif isinstance(key, basestring):
            if key in self.__maps:
                index = self.__maps.index(key)
                map = str(self.__maps[index])
                weights = numpy.array(self.__weights[index])
        else:
            print('Cannot find {} in this WeightObject. Please be sure to pass valid str or int'.format(key))

        return (map, weights)

    def normalize(self, maps=None):
        '''
        This method is used to normalize each maps weights
        :return:
        '''
        if maps:
            maps = common.toList(maps)
            for map in maps:
                weight_list = self.__weights[self.__maps.index(maps)]
                value_index_list = numpy.where(weight_list[0] > 1)[0]
                for index in value_index_list:
                    weights[index] = 1
        else:
            value_index_list = numpy.where(self.__weights[0] > 1)[0]
            for index in value_index_list:
                self.__weights[0][index] = 1

    def next(self):
        '''
        This will iterate through each index
        '''
        try:
            result = self.__maps[self._index]
        except IndexError:
            self._index = 0
            raise StopIteration
        self._index += 1
        return result

    # Get
    def getMaps(self):
        '''
        This will return the list of maps 

        :return: List of maps stored on this weight object
        :type: list
        '''
        return self.__maps

    def getWeights(self, maps=None):
        '''
        This will return the list of weights 

        :return: List of maps stored on this weight object
        :type: list
        '''
        if not maps:
            return self.__weights
        else:
            mapList = common.toList(maps)
            return [self.__weights[self.__maps.index(map)] for map in mapList if map in self.__maps]

    # Set
    def setMaps(self, value):
        '''
        This will take in a value which should be a list of maps you want to set 

        :param value: Must be a list of maps.
        :type value: list
        '''
        self.__maps = common.toList(value)

    def setWeights(self, value):
        '''
        This will take in a value which should be a list of numpy arrays you want to in the order
        which you have given the maps. These two list should be the same length.

        :param value: Must be a list of numpy arrays.
        :type value: list
        '''
        weightList = common.toList(value)
        self.__weights = list()
        for weights in weightList:
            if isinstance(weights, numpy.ndarray):
                self.__weights.append(weights)
                continue
            self.__weights.append(numpy.array(weights))

