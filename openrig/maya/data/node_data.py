'''
This is our json module.
'''
import openrig.maya.data.maya_data as maya_data
from collections import OrderedDict
import maya.cmds as mc

class NodeData(maya_data.MayaData):
    '''
    handle mostly storing data for transform nodes.
    '''
    def __init__(self):
        '''
        Constructor for the node data class
        '''
        # set class attributes defaults
        super(NodeData, self).__init__()

    def gatherData(self,node):
        '''
        This method will gather data for the node that is passed in as an argument. It will
        store this data on the self._data member/attribute on the class.

        :param node: Node you wish to gather the data for.
        :type node: str
        '''
        super(NodeData, self).gatherData(node)

        data = OrderedDict()
        for attr in ['translate','rotate','scale', 'selectHandle']:
            data[attr] = [round(value, 4) for value in mc.getAttr("{0}.{1}".format(node,attr))[0]]

        data['world_translate'] = mc.xform(node, q=True, ws=True, t=True)
        data['world_rotate'] = mc.xform(node, q=True, ws=True, ro=True)

        data['rotateOrder'] = mc.getAttr("{0}.rotateOrder".format(node))

        self._data[node].update(data)

    def applyData(self, nodes, attributes=None, worldSpace=False):
        '''
        Applies the data for the given nodes. There is an optional arguments so you 
        can apply data only to specific attributes.

        :param nodes: Array of nodes you want to apply the data to.
        :type nodes: list | tuple

        :param attributes: Array of attributes you want to apply the data to.
        :type attributes: list | tuple
        '''
        gather_attributes_from_file = False
        for node in nodes:
            if not self._data.has_key(node):
                continue
            if not attributes:
                gather_attributes_from_file = True
                attributes = self._data[node].keys()

            # if world space is passed, we will apply translate and rotate in world space as long as
            # it was stored out that way. Otherwise we will apply using local.
            if worldSpace:
                if 'translate' in attributes and self._data[node].has_key('world_translate'):
                    mc.xform(node, ws=True, t=self._data[node]['world_translate'])
                    attributes.pop(attributes.index('translate'))
                if 'rotate' in attributes and self._data[node].has_key('world_rotate'):
                    mc.xform(node, ws=True, ro=self._data[node]['world_rotate'])
                    attributes.pop(attributes.index('rotate'))

            for attribute in attributes:
                if self._data[node].has_key(attribute) and attribute in mc.listAttr(node):
                    setAttr = True
                    for attr in mc.listAttr("{}.{}".format(node, attribute)):
                        if mc.listConnections('{0}.{1}'.format(node,attr), d=False, s=True) or \
                            mc.getAttr('{0}.{1}'.format(node,attr),l=True):
                                setAttr = False
                                break
                    if not setAttr:
                        continue
                    value = self._data[node][attribute]
                    if isinstance(value, (list,tuple)):
                        mc.setAttr('{0}.{1}'.format(node,attribute),*value)    
                    elif isinstance(value,basestring):
                        mc.setAttr('{0}.{1}'.format(node,attribute),value, type="string")
                    else:
                        mc.setAttr('{0}.{1}'.format(node,attribute),value)

            # clear the attributes if we're getting them from the file
            if gather_attributes_from_file:
                attributes = None


