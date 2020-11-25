"""Deformer utilities"""

import maya.cmds as mc
import maya.mel as mm
# showtools Modules
from openrig.maya import skinCluster
from openrig.maya import cluster
from openrig.maya import weights

def arrangeToTop(geo, deformer):
    """Arrange given deformer on top of the deformer stack for given geometry(s).

    :param geo: geometry to act on
    :type geo: list | str

    :param deformer: deformer name to arrange
    :type deformer: str
    """
    if not isinstance(geo, list): geo = [geo]
    
    for g in geo:
        # get deformers
        deformers = getDeformerStack(g)
        
        if len(deformers) < 2:
            mc.warning('Only one deformer found on geometry "%s".  Nothing to arrange.' % g)
            continue
        
        # check deformer
        if not deformer in deformers:
            mc.warning('Provided deformer "%s" was not found on geometry "%s"' % (deformer, g))
            continue
        
        # remove deformer from list
        deformers = [d for d in getDeformerStack(g) if d != deformer]
        
        # arrange
        mc.reorderDeformers(deformers[0], deformer, g)
        mc.reorderDeformers(deformer, deformers[0], g)


def arrangeToBottom(geo, deformer):
    """Arrange given deformer on bottom of the deformer stack for given geometry(s).

    :param geo: geometry to act on
    :type geo: list | str

    :param deformer: deformer name to arrange
    :type deformer: str
    """
    if not isinstance(geo, list): geo = [geo]
    
    for g in geo:
        # get deformers
        deformers = getDeformerStack(g)
        
        if len(deformers) < 2:
            mc.warning('Only one deformer found on geometry "%s".  Nothing to arrange.' % g)
            continue
        
        # check deformer
        if not deformer in deformers:
            mc.warning('Provided deformer "%s" was not found on geometry "%s"' % (deformer, g))
            continue
        
        # remove deformer from list
        deformers = [d for d in getDeformerStack(g) if d != deformer]

        # arrange
        mc.reorderDeformers(deformers[-1], deformer, g)      


def arrangeToType(geo, deformer, deformer_type, first=False, after=True):
    """Arrange given deformer before or after deformer type.

    Set first=True to arrange to the first found instance of given type (bottom of the stack).  By
    default it will arrange the deformer to the last found instance of given type (top of the stack).

    Set after=False to arrange before the found deformer type (below in the stack).  By default it
    will arrange the deformer after the found deformer type (above in the stack).

    :param geo: geometry to act on
    :type geo: list | str

    :param deformer: deformer name to arrange
    :type deformer: str

    :param deformer_type: Maya deformer type
    :type deformer_type: str

    :param first: whether to arrange the deformer to the first or last found deformer of given type
    :type first: bool

    :param after: whether to arrange the deformer before or after the found of given type
    :type after: bool
    """
    if not isinstance(geo, list): geo = [geo]
    
    for g in geo:
        # get deformers of type
        deformers = [d for d in mm.eval('findRelatedDeformer("%s")' % g) if mc.nodeType(d) == deformer_type]
        
        if len(deformers) < 2:
            mc.warning('Only one deformer found on geometry "%s".  Nothing to arrange.' % g)
            continue
        
        # check deformer
        if not deformer in deformers:
            mc.warning('Provided deformer "%s" was not found on geometry "%s"' % (deformer, g))
            continue
        
        # get neighbor
        neighbor = deformers[0] if first else deformers[-1]                
        
        # arrange
        mc.reorderDeformers(neighbor, deformer, g)
        if after:
            mc.reorderDeformers(deformer, neighbor, g)

    
def arrangeSlide(geo, deformer, up=True):
    """Arrange given deformer by sliding up or down in the list.

    :param geo: geometry to act on
    :type geo: list | str

    :param deformer: deformer name to arrange
    :type deformer: str

    :param up: whether to slide up or down in the list (default: True)
    :type up: bool
    """
    if not isinstance(geo, list): geo = [geo]

    for g in geo:
        # get deformers
        deformers = getDeformerStack(g)
        
        if len(deformers) < 2:
            mc.warning('Only one deformer found on geometry "%s".  Nothing to arrange.' % g)
            continue
        
        # check deformer
        if not deformer in deformers:
            mc.warning('Provided deformer "%s" was not found on geometry "%s"' % (deformer, g))
            continue

        # get neighbor
        index = deformers.index(deformer)
        if index == 0 and up: return
        if index == len(deformers) - 1 and not up: return
        
        neighbor = deformers[index - 1] if up else deformers[index + 1]

        # arrange
        if up:
            mc.reorderDeformers(deformer, neighbor, g)
        else:
            mc.reorderDeformers(neighbor, deformer, g)            
        

def setDeformerOrder(geo, order, top=True):
    """Sets the deformer stack in the order given from the bottom of the deformer stack. Any 
    deformers not explicitly listed in the given "order" list will be ignored.  As a result
    unspecified deformers will appear at the top of the stack.
    
    :param geo: geometry object name
    :type geo: str
    
    :param order: list of deformer names in the desired order
    :type order: list
    
    :param top: whether to start deformer order from the top (True)
    :type top: bool
    """
    if top:
        order.reverse()
        for deformer in order:
            arrangeToTop(geo, deformer)
    else:
        for deformer in order:
            arrangeToBottom(geo, deformer)
    
        
def getDeformerStack(geo, ignoreTypes=['tweak']):
    """Returns deformers in order for given geometry object.
    
    :param geo: geometry object name
    :type geo: str
    
    :param ignoreTypes: deformer types to exclude from the list
    :type ignoreTypes: list

    :returns: a list of deformers in order
    :rtype: list
    """
    # list history to get all inputs in order
    history = mc.listHistory(geo, interestLevel=1, pruneDagObjects=True)
    
    # find related deformers for a more concise list of deformers
    deformers = mm.eval('findRelatedDeformer("%s")' % geo)
    
    # return history items that are in the deformers list
    return [d for d in history if d in deformers and not mc.nodeType(d) in ignoreTypes]


def transferDeformers(source, target, deformerTypes = ["skinCluster"],
                        surfaceAssociation="closestPoint"):
    '''
    This will transfer all deformers and weights. If it's the same

    :param source: The geomertry you are transfer from
    :type source:  str

    :param target: The geometry you want to transfer to
    :type target: str | list

    :param surfaceAssociation: How to copy the weights from source to target available values 
                                are "closestPoint", "rayCast", or "closestComponent"
    :type surfaceAssociation: str
    '''
    # do some error checking
    hist = [node for node in mc.listHistory(source, pdo=True, interestLevel=1) if mc.nodeType(node) in deformerTypes]
    if hist:
        if 'skinCluster' in deformerTypes:
            skinCluster.transferSkinCluster(source, target, surfaceAssociation)
        elif 'cluster' in deformerTypes:
            for cls in cluster.getClusters(source):
                cls.transferCluster(source, target, cluster, handle=True, surfaceAssociation="closestPoint", createNew=True)

def copyDeformer(deformer, target):
    '''
    Make a copy of the passed deformers on the target

    :param target: Target transform of shape
    :param deformers: deformers to copy
    :return: Copied deformers
    '''
    deformerOrder= mc.ls(mc.listHistory(target, pdo=1, il=1), type="geometryFilter")
    orderIndex = deformerOrder.index(deformer)
    if mc.nodeType(deformer) == 'wire':
        # Get data
        curve = mc.wire(deformer, q=1, wire=1)[0]
        baseCurve = mc.listConnections(deformer+'.baseWire[0]', p=1)[0]
        # Note: wire command has issues when passing the shape, so get the transform
        curve = mc.listRelatives(curve, p=1)[0]
        rotation = mc.getAttr(deformer+'.rotation')
        dropOffDistance = mc.getAttr(deformer+'.dropoffDistance[0]')
        mc.select(cl=1)
        newDeformer = mc.wire(target,
                               groupWithBase=False,
                               envelope=1.00,
                               crossingEffect=0.00,
                               localInfluence=0.00,
                               wire=curve,
                               name="{}_wire".format(target))[0]
        # Replace base curve
        newBaseCurve = mc.listConnections(newDeformer+'.baseWire[0]')
        mc.connectAttr(baseCurve, newDeformer+'.baseWire[0]', f=1)
        mc.delete(newBaseCurve)

        # set the default values for the wire deformer
        mc.setAttr("{}.rotation".format(newDeformer), rotation)
        mc.setAttr("{}.dropoffDistance[0]".format(newDeformer), dropOffDistance)

    if mc.nodeType(deformer) == 'cluster':
        mc.select(cl=1)
        deformerWts = weights.getWeights(deformer, geometry=target)
        bindPreMatrixAttr = mc.listConnections('{}.bindPreMatrix'.format(deformer), source=True, plugs=True)[0]
        handle = mc.listConnections('{}.matrix'.format(deformer), source=True)[0]
        newDeformer = mc.cluster(target, name="{}_{}".format(target, deformer), wn=[handle,handle])[0]
        mc.connectAttr('{}.worldMatrix'.format(target), '{}.geomMatrix[0]'.format(newDeformer), f=True)
        mc.connectAttr(bindPreMatrixAttr, '{}.bindPreMatrix'.format(newDeformer), f=True)
        weights.setWeights(newDeformer,deformerWts, geometry=target)

    # Reorder deformer
    if orderIndex:
        mc.reorderDeformers(deformerOrder[orderIndex-1], newDeformer, target)

        return newDeformer

def makeDeformerUnique(deformer, target):
    '''

    :param deformer:
    :param target:
    :return:
    '''
    copyDeformer(deformer, target)
    mc.deformer(deformer, e=1, rm=1, g=target)

def getGeoIndex(deformer, geo):
    '''
    For the given deformer find what index the given geo is connected to.
    :param deformer:
    :param geo:
    :return:
    '''
    geo = getShape(geo)
    if not geo:
        return
    deformed_geos = mc.deformer(deformer, q=1, g=1, gi=1)
    deformed_indexes = mc.deformer(deformer, q=1, gi=1)
    for n in range(len(deformed_geos)):
        if deformed_geos[n] == geo:
            return(int(deformed_indexes[n]))

def getGeoInputAttr(deformer, geo):
    '''
    Given the deformer and geo find the full attribute name for the deformer input
    :param deformer:
    :param geo:
    :return:
    '''

    single = '{}.inputGeometry'.format(deformer)
    multi = '{}.input'.format(deformer)
    full_attr = None

    if mc.objExists(single):
        full_attr = single

    if mc.objExists(multi):
        index = getGeoIndex(deformer, geo)
        full_attr = '{}[{}].inputGeometry'.format(multi, index)
        if not mc.objExists(full_attr):
            return
        # If there is a group parts return that instead
        con = mc.listConnections(full_attr)
        if mc.nodeType(con[0]) == 'groupParts':
            full_attr = '{}.inputGeometry'.format(con[0])

    # Verify geo is deformed by the deformer
    return full_attr

def getGeoOutputAttr(deformer, geo):
    '''
    Given the deformer and geo find the full attribute name for the deformer input
    :param deformer:
    :param geo:
    :return:
    '''
    full_attr = '{}.outputGeometry'.format(deformer)
    if not mc.objExists(full_attr):
        return

    multi = mc.getAttr(full_attr, mi=1)

    if multi:
        index = getGeoIndex(deformer, geo)
        full_attr = '{}[{}]'.format(full_attr, index)

    return full_attr

def getShape(node):
    '''
    Return the shape for the given node, pass the node through if it is already a geo shape
    :param node:
    :return:
    '''
    shape_types = ['mesh', 'nurbsSurface', 'nurbsCurve', 'subdiv']
    node_type = mc.nodeType(node)

    if node_type in shape_types:
        return(node)

    if node_type == 'transform':
        shape = mc.listRelatives(node, s=1, ni=1)
        if shape:
            return(shape[0])
