'''
This module is for dealing with shape nodes in Maya
'''
import maya.cmds as mc
import maya.mel as mm
import numpy
from showtools.maya import attr
from showtools.maya import hierarchy

def getPointCount(shape):
    '''
    Gets the point count of a nurbsCurve or mesh
    :param shape:
    :return: Int
    '''

    if mc.nodeType(shape) == 'transform':
        shape = mc.listRelatives(shape, s=1, ni=1)[0]

    shape_type = mc.nodeType(shape)
    if shape_type == 'mesh':
        pnt_count = mc.polyEvaluate(shape, v=1)
    if shape_type == 'nurbsCurve':
        pnt_count = int(mc.ls('{}.cv[*]'.format(shape))[0].split(':')[1][:-1])
        pnt_count +=1

    return pnt_count

GEOTYPES = ['mesh', 'nurbsSurface', 'nurbsCurve', 'subdiv']
SHAPEPLUGS = {'mesh': ('outMesh', 'inMesh'),
              'nurbsSurface': ('outSurface', 'create'),
              'nurbsCurve': ('outCurve', 'create'),
              'subdiv': ('outSubdiv', 'create')}

              
def connectShape(source, target):
    """Connects shape nodes for valid geometry types (GEOTYPES)

    :param source: source object (transform or shape node)
    :type source: str

    :param target: target object (transform or shape node)
    :type source: str
    """
    # check types
    sourceType = getType(source)
    targetType = getType(target)
    
    if not all(o in GEOTYPES for o in [sourceType, targetType]):
        return
    
    if not sourceType == targetType:
        return
    
    # connect shapes
    outPlug = SHAPEPLUGS[sourceType][0]
    inPlug = SHAPEPLUGS[sourceType][1]
    mc.connectAttr(source+'.'+outPlug, target+'.'+inPlug, f=True)
    
    # force dirty
    mc.refresh()


def disconnectShape(source, target):
    """Disconnects shape nodes for valid geometry types (GEOTYPES)

    :param source: source object (transform or shape node)
    :type source: str

    :param target: target object (transform or shape node)
    :type source: str
    """
    # check types
    sourceType = getType(source)
    targetType = getType(target)
    
    if not all(o in GEOTYPES for o in [sourceType, targetType]):
        return
    
    if not sourceType == targetType:
        return

    # disconnect shapes
    outPlug = SHAPEPLUGS[sourceType][0]
    inPlug = SHAPEPLUGS[sourceType][1]
    mc.disconnectAttr(source+'.'+outPlug, target+'.'+inPlug)
    
    # force dirty
    mc.refresh()


def getType(obj):
    """Returns the type of shape it is.  If the object has a shape node it returns it as the object's
    type.  For example if the object is a polygon it will return 'mesh' for either the shape node or
    the transform node.

    :param obj: object name to get type for
    :type obj: str
    """
    objType = mc.nodeType(obj)
    if objType == 'transform':
        shapes = mc.listRelatives(obj, s=True, f=True) or []
        shapeTypes = set()
        for shape in shapes:
            shapeTypes.add(mc.nodeType(shape))

        if len(shapeTypes) > 1:
            objType = 'mixed'
        elif shapeTypes:
            objType = list(shapeTypes)[0]

    return str(objType)


def getShapes(obj):
    """Return the shape nodes of given object. If the object is a transform it returns the shape(s)
    directly under it. If it is a shape it returns itself.
    
    :param obj: object to get shape for
    :type obj: str
    
    :returns: shape node if there is one
    :rtype: list
    """
    if mc.nodeType(obj) != 'transform':
        return mc.ls(obj, dag=True, s=True, ni=True)
    else:
        return mc.listRelatives(obj, s=True, ni=True) or []
    

def nukeHistory(objects, keepTransforms=False, keepAttrs=False, keepUVs=False):
    """Deletes history and everything else by creating a new node in the place of the old one.  Has
    options to preserve transform values (translate, rotate, scale) and attributes.  Attributes kept
    are limited to user-defined and transform types.
    
    :param objects: list of objects to nuke
    :type objects: list
    
    :param keepTransforms: whether to apply old transform values on the new objects
    :type keepTransforms: bool
    
    :param keepAttrs: whether to apply existing attributes and values to new objects
    :type keepAttrs: bool
    """
    # get objects as list
    if not isinstance(objects, list): objects = [objects]
    
    # nuke history
    for obj in objects:
        # get type
        objType = getType(obj)
        if not objType in GEOTYPES:
            return

        # get shape node
        shapeNode = mc.listRelatives(obj, s=True)[0]
                
        # get transform graph data
        graph = hierarchy.getTransformGraph([obj, shapeNode])
        
        # get attr data
        transformAddAttrCmds = list()
        transformSetAttrCmds = list()
        shapeAddAttrCmds = list()
        shapeSetAttrCmds = list()
        if keepAttrs:
            attrs = attr.USER(obj)
            if keepTransforms: attrs += attr.TRANSFORMS
            attrs = [obj+'.'+a.split('.')[0] for a in attrs]
            
            transformAddAttrCmds = attr.getAddAttrCmds(attrs)
            transformSetAttrCmds = attr.getSetAttrCmds(attrs)
            
            attrs = [shapeNode+'.'+a.split('.')[0] for a in attr.USER(shapeNode) or []]
            shapeAddAttrCmds = attr.getAddAttrCmds(attrs)
            shapeSetAttrCmds = attr.getSetAttrCmds(attrs)
        
        # delete history
        mc.delete(obj, ch=True)

        # freeze transforms
        if not keepTransforms:
            # prep transform attrs
            for a in attr.TRANSFORMS:
                mc.setAttr(obj+'.'+a, l=False)
                connections = mc.listConnections(obj+'.'+a, c=True, p=True)
                if connections:
                    mc.disconnectAttr(connections[1], connections[0])

            # freeze
            mc.makeIdentity(obj, apply=True, t=True, r=True, s=True)

        # create new
        name = graph[0]['name']
        newTransform = mc.createNode('transform', n=name+'_TEMP')
        newShapeNode = mc.createNode(objType, n=newTransform+'Shape', p=newTransform)
        
        # transfer shape
        connectShape(shapeNode, newShapeNode)
        disconnectShape(shapeNode, newShapeNode)

        # delete original
        mc.delete(obj)
        
        # parent
        parent = graph[0]['parent']
        if parent:
            mc.parent(newTransform, parent)
        
        # rename
        newTransform = mc.rename(newTransform, name)
        newShapeNode = mc.rename(mc.listRelatives(newTransform, s=True)[0], graph[1]['name'])
        
        # delete UVs
        if keepUVs is False:
            uvSets = mc.polyUVSet(newShapeNode, q=True, allUVSets=True)
            if len(uvSets) > 1:
                for uvSet in uvSets[1:]:
                    mc.polyUVSet(newShapeNode, uvSet=uvSet, delete=True)
            mc.polyMapDel(newShapeNode)
        
        # reorder
        neighbors = graph[0]['neighbors']
        if neighbors[0]:
            hierarchy.reorderTo(newTransform, neighbors[0])
        elif neighbors[1]:
            hierarchy.reorderTo(newTransform, neighbors[1], after=False)
                
        # restore attrs
        if keepAttrs:
            attr.applyAddAttrCmds(transformAddAttrCmds)
            attr.applySetAttrCmds(transformSetAttrCmds)
            
            attr.applyAddAttrCmds(shapeAddAttrCmds)
            attr.applySetAttrCmds(shapeSetAttrCmds)
        
        # restore default shading group
        mc.sets(obj, e=True, forceElement='initialShadingGroup')
        
    mc.select(objects)


def getDeltas(base, target): 
    '''
    Get deltas between two shapes. This will return the magnitude which will be the difference
    between the two points.

    :param base: Base object
    :type base: str
    
    :param target: Target object
    :type target: str

    :returns: List of deltas in the order of point index
    :rtype: list
    '''
    if not mc.objExists(base) or not mc.objExists(target):
        raise RuntimeError("Either {} or {} doesn't exist in the current Maya session".format(base, target))
     
    bs = mc.blendShape(target, base, w=[0, 1])[0] 
    mc.pointPosition(base+'.vtx[0]') # Enforce refresh
    delta_list = mc.getAttr(bs+'.it[0].itg[0].iti[6000].ipt')
    index_list = mc.getAttr(bs+'.it[0].itg[0].iti[6000].ict')                                
    mc.delete(bs)
    if not index_list:
        return([])
 
    # =============================================== 
    # Point array 
    # =============================================== 

    count = len(index_list) 
    index_flat_list = list() 
    for n in index_list: 
        index_flat_list.append(target+'.'+n) 
     
    index_flat_list = mc.ls(index_flat_list, fl=1) 
    index_only_list = list() 
     
    for n in index_flat_list: 
        index_only_list.append(int(n.split('[')[1][:-1])) 
     
    # =============================================== 
    # Weight array 
    # ===============================================     
    weight_list = numpy.zeros(len(mc.ls("{}.cp[*]".format(target),fl=True)), dtype=float)                      
    for n in range(len(index_flat_list)): 
        weight_list[index_only_list[n]] = round(delta_list[n][0], 4)

    return weight_list


def getDeltaIndices(base, target, objName=False):
    '''
    Get indices of the points with different positions between the two goes
    between the two points.

    :param base: Base object
    :type base: str

    :param target: Target object
    :type target: str

    :param objName: Include the target name in the return
    :type objName: bool

    :returns: List of indices
    :rtype: list
    '''
    if not mc.objExists(base) or not mc.objExists(target):
        raise RuntimeError("Either {} or {} doesn't exist in the current Maya session".format(base, target))

    bs = mc.blendShape(target, base, w=[0, 1])[0]
    mc.pointPosition(base+'.vtx[0]')  # Enforce refresh
    index_list = mc.getAttr(bs+'.it[0].itg[0].iti[6000].ict')
    mc.delete(bs)

    # ===============================================
    # Flatten and return only indices
    # ===============================================

    if not index_list:
        return []
    index_flat_list = [target+'.'+x for x in index_list]
    index_flat_list = mc.ls(index_flat_list, fl=1)
    if objName:
        return index_flat_list
    index_only_list = [int(x.split('[')[1][:-1]) for x in index_flat_list]

    return index_only_list
