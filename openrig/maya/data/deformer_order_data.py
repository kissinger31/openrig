'''
This is going to work on nodes in the scene.
'''
from collections import OrderedDict

import maya.cmds as mc
import showtools.maya.data.maya_data as maya_data

class DeformerOrderData(maya_data.MayaData):
    '''
    This class is created to store and apply data for deformer order.
    '''
    def __init__(self):
        '''
        The constructor for the sdk class.
        '''
        super(DeformerOrderData, self).__init__()

    def gatherData(self, node):
        '''
        This method will gather data for the node that is passed in as an argument. It will
        store this data on the self._data member/attribute on the class.

        :param node: Node you wish to gather the data for.
        :type node: str
        '''
        super(DeformerOrderData, self).gatherData(node)

        data = OrderedDict()
        data["deformerOrder"] = mc.ls(mc.listHistory(node, il=2, pdo=1), type='geometryFilter') or []
        if data["deformerOrder"]:
            self._data[node].update(data)
        else:
            if self._data.has_key(node):
                self._data.pop(node)

    def applyData(self, nodes):
        '''
        Applies the data for the given nodes. There is an optional arguments so you 
        can apply data only to specific nodes.

        :param nodes: Array of nodes you want to apply the data to.
        :type nodes: list | tuple
        '''
        # loop through the nodes and apply the data.
        for node in nodes:
            if self._data.has_key(node):
                if len(self._data[node]["deformerOrder"]) > 1:
                    orderCurrent = mc.ls(mc.listHistory(node, il=2, pdo=1), type='geometryFilter') or []
                    if not orderCurrent:
                        continue
                    orderStored = self._data[node]["deformerOrder"]
                    for index, deformer in enumerate(orderStored):
                        if index == len(orderStored)-1:
                            break
                        nextDeformer = orderStored[index+1]
                        # Check if the deformers are on the object
                        if not set([nextDeformer, deformer]).issubset(orderCurrent):
                            continue

                        # Test if the deformer order is all ready correct
                        indexNextDeformerCurrent = orderCurrent.index(nextDeformer)
                        indexCurrent = orderCurrent.index(deformer)
                        if indexNextDeformerCurrent != indexCurrent+1:
                            mc.reorderDeformers(deformer, nextDeformer, [node])
                            # Update order current so it can be tested
                            orderCurrent = mc.ls(mc.listHistory(node, il=2, pdo=1), type='geometryFilter') or []