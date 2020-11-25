'''
This is going to work on Maya sets in the scene.
'''
from collections import OrderedDict
import maya.cmds as mc
import openrig.maya.data.maya_data as maya_data

class SetsData(maya_data.MayaData):
    '''
    This class is created to store and apply data for Maya sets.
    '''
    def __init__(self):
        '''
        The constructor for the sets class.
        '''
        super(SetsData, self).__init__()

    def gatherData(self, node, parent=str()):
        '''
        This method will gather data for the node that is passed in as an argument. It will
        store this data on the self._data member/attribute on the class.

        :param node: Node you wish to gather the data for.
        :type node: str
        '''
        super(SetsData, self).gatherData(node)

        data = OrderedDict()
        # first check to make sure it's an objectSet node type being passed in.
        if not mc.ls(node, type='objectSet'):
            raise RuntimeError("{} is not an objectSet that is used for sets.".format(node))

        # get the members of a set
        member_list = mc.ls(mc.sets(node, q=True),fl=True)
        sets_type = mc.nodeType(node)

        # if no parent is passed, see if node is a member of another set.
        if not parent:
            object_set_list = mc.ls(type='objectSet')
            for object_set in object_set_list:
                if mc.sets(node, isMember=object_set):
                    parent = object_set
                    break

        for member in member_list:
            # if the member we're storing is an objectSet, we want to also store that and it's members.
            # we will recursively run through until we come back.
            if 'objectSet' in mc.nodeType(member, i=True):
                self.gatherData(member, parent=node)

        # update the data dictionary
        data.update({'members': member_list,
                     'parent': parent,
                     'type': sets_type})

        self._data[node].update(data)

    def applyData(self, nodes):
        '''
        Applies the data for the given nodes.

        :param nodes: Array of sets you want to apply the data to.
        :type nodes: list | tuple
        '''
        # loop through the nodes and apply the data.
        for node in nodes:
            # check to make sure the node we're looking for exist in the data
            if self._data.has_key(node):
                # check and see if there is a parent set stored for this node
                parent = self._data[node]['parent']
                # if there is a parent stored and it exist. We will recursively run through parents until we come back.
                if self._data.has_key(parent):
                    if not mc.objExists(parent):
                        self.applyData([parent])
                # select the members that exist in the scene and add create the set
                if not mc.objExists(node):
                    mc.sets(mc.ls(self._data[node]['members']), name=node)
                else:
                    member_list = mc.ls(mc.sets(node, q=True), fl=True)
                    new_member_list = [member for member in mc.ls(self._data[node]['members']) if member not in member_list]
                    if new_member_list:
                        mc.sets(mc.ls(new_member_list), e=True, add=node)
                # if there is a parent. We will be sure to store this node under it's parent node.
                if mc.objExists(parent):
                    mc.sets(node, e=True, fe=parent)


class CreaseSetsData(SetsData):
    '''
    This class is created to store and apply data for Maya sets.
    '''
    def __init__(self):
        '''
        The constructor for the sets class.
        '''
        super(CreaseSetsData, self).__init__()

    def gatherData(self, node, parent=str()):
        '''
        This method will gather data for the node that is passed in as an argument. It will
        store this data on the self._data member/attribute on the class.

        :param node: Node you wish to gather the data for.
        :type node: str
        '''
        super(CreaseSetsData, self).gatherData(node)

        data = OrderedDict()


        # update the data dictionary
        data.update({'creaseLevel': mc.getAttr('{}.creaseLevel'.format(node))})

        self._data[node].update(data)

    def applyData(self, nodes):
        '''
        Applies the data for the given nodes.

        :param nodes: Array of sets you want to apply the data to.
        :type nodes: list | tuple
        '''
        # loop through the nodes and apply the data.
        for node in nodes:
            # check to make sure the node we're looking for exist in the data
            if self._data.has_key(node):
                if not mc.objExists(node):
                    mc.createNode('creaseSet', name=node)
                # check and see if there is a parent set stored for this node
                parent = self._data[node]['parent']
                # if there is a parent stored and it exist. We will recursively run through parents until we come back.
                if self._data.has_key(parent):
                    if not mc.objExists(parent):
                        self.applyData([parent])
                # select the members that exist in the scene and add create the set
                mc.sets(*mc.ls(self._data[node]['members']), fe=node)
                # if there is a parent. We will be sure to store this node under it's parent node.
                if mc.objExists(parent):
                    mc.sets(node, e=True, fe=parent)
                mc.setAttr('{}.creaseLevel'.format(node), self._data[node]['creaseLevel'])

