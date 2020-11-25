"""Maya wrap deformer functions."""
import maya.cmds as mc
import maya.mel as mm
from showtools.maya import common
from showtools.maya import naming


def doWrapTo():
    """Performs a wrapTo based on the selected objects in-scene."""
    # get selection
    selection = mc.ls(sl=True, fl=True)
    
    # get faces, geo, and influence
    faces = list()
    geo = list()
    influence = None
    for item in selection:
        if '.f' in item:
            # get face index
            face = int(item.split('.f[')[-1].replace(']', ''))
            faces.append(face)
            
            # get influence
            inf = item.split('.')[0]
            if not influence:
                influence = inf
            elif not influence == inf:
                raise Exception('Can only wrap to faces from one influence object.')
        else:
            geo.append(item)
    
    if not influence:
        influence = geo.pop(-1)
    
    # wrap
    wrapTo(geo=geo, influence=influence, faces=faces)


def wrapTo(geo, influence, faces=None):
    """Wraps given geometry object(s) to the given influence geometry object. If faces are specified
    only those faces will be used as influences.
    
    :param geo: list of geometry names to wrap
    :type geo: list | str
    
    :param influence: name of geometry to use for base wrap
    :type influence: str
    
    :param faces: list of faces to use as influence (None)
    :type faces: str| list | None
    """
    # get current frame
    frame = 'f'+str(int(mc.currentTime(q=True))).zfill(4)
    
    # duplicate geo
    if not isinstance(geo, list): geo = [geo]
    geoDup = mc.duplicate(geo)
    wrapGeo = list()
    for name, g in zip(geo, geoDup):
        if mc.listRelatives(g, p=True):
            g = mc.parent(g, w=True)
        g = mc.rename(g, '%s_%s_warpGeo1' % (name, frame))
        wrapGeo.append(g)
       
    # use faces
    if faces:
        # duplicate influence
        if not isinstance(influence, basestring):
            raise Exception('Influence must be a single object')
        influenceDup = mc.duplicate(influence)[0]
        if mc.listRelatives(influenceDup, p=True):
            influenceDup = mc.parent(influenceDup, w=True)
        influenceDup = mc.rename(influenceDup, '%s_%s_wrapInfluence1' % (influence, frame))
        
        # use given faces only
        influenceDupFaces = set([influenceDup+'.f[%s]' % str(f) for f in faces])
        allFaces = set(mc.ls(influenceDup+'.f[*]', fl=True))
        toDelete = allFaces-influenceDupFaces
        mc.delete(list(toDelete))
        
        # wrap duplicate faces back to influence
        # TODO: rewrite this so it doesn't rely on selection...
        mc.select(influenceDup, influence, r=True)
        influenceWrap = mm.eval('doWrapArgList "7" { "1","0","0", "2", "0", "0", "0", "0" }')[0]
        mc.select(cl=True)

        # un-parent base
        influenceBase = mc.listConnections(influenceWrap + '.basePoints')
        if influenceBase:
            parent = mc.listRelatives(influenceBase, p=True)
            if parent:
                mc.parent(influenceBase[0], world=True)
        
        influence = influenceDup
        mc.hide(influence)
    
    # wrap geo to influence
    # TODO: rewrite this so it doesn't rely on selection...
    mc.select(wrapGeo, influence, r=True)
    wrap = mm.eval('doWrapArgList "7" { "1","0","0", "2", "0", "0", "0", "0" }')[0]
    mc.select(cl=True)
    mc.hide(wrapGeo)
    
    # un-parent base
    base = mc.listConnections(wrap + '.basePoints')
    if base:
        parent = mc.listRelatives(base, p=True)
        if parent:
            mc.parent(base[0], world=True)
    
    # blend wrap geo back into geo
    for w, g in zip(wrapGeo, geo):
        name = '%s_%s_wrapToBlend1' % (naming.getUniqueName(w), frame)
        blend = mc.blendShape(w, g, w=[0,1], name=name, o='world')[0]
        mc.setAttr(blend+'.origin', 1)
        
        # link blendshape
        mc.addAttr(blend, ln='wrapTo', at='message')
        mc.connectAttr(wrap+'.message', blend+'.wrapTo')
        
        # link geo
        if not mc.objExists(g+'.wrapTo'):
            mc.addAttr(g, ln='wrapTo', at='message')
        mc.connectAttr(wrap+'.message', g+'.wrapTo', f=True)


def transferWrap(source, target, deformer):
    """
    This will transfer wrap from one mesh to another. If the target doesn't have a
    wrap on it, it will create a new wrap. Then once there is a wrap
    We will copy weights over.

    :param source: The geomertry you are transfer from
    :type source:  str

    :param target: The geometry you want to transfer to
    :type target: str | list

    """
    # do some error checking
    if not mc.objExists(source):
        raise RuntimeError('The source mesh "{}" does not exist in the current Maya session.'.format(source))

    # first we will turn the target into a list if it's not already a list
    targetMeshList = common.toList(target)

    # make sure we have a wrap on the source mesh
    sourceWraps = getWraps(source)
    wrapList = list()
    if deformer not in sourceWraps:
        mc.warning('The source mesh "{}" is missing "{}"'.format(source, deformer))
        return

    # Loop through target meshes
    for targetMesh in targetMeshList:
        if not mc.objExists(targetMesh):
            mc.warning('The target mesh "{}" does not exist in the current Maya session.'.format(target))
            continue

        # check to see if there is a wrap already  on the target mesh
        hist = getWraps(targetMesh)
        if deformer in hist:
            mc.warning('The target mesh "{}" is being deformed by "{}", aborting.'.format(targetMesh, deformer))
            continue

        name = "{}_bs".format(targetMesh)
        # Build wrap
        target_bs = mc.wrap(targetMesh, n=deformer)[0]
        targets = getTargetNames(deformer)
        for target in targets:
            addTarget(target_bs, name=target)

        print('source', source, 'target', targetMesh)
        print('targets', targets)
        #wrapList.append(hist[0])

    return wrapList


def createWrap(sourceGeo, targetGeo, exclusiveBind=0):
    """
    Create wrap deformer

    Main call from
    C:/Program Files/Autodesk/Maya2018/scripts/others/performCreateWrap.mel

    :param sourceGeo: The geo that is being controlled by the wrap
    :param targetGeo: The geo that is being wrapped to.
    :param exclusiveBind: Only bind to closest points, fastest option.
    :return:
    """
    sel = mc.ls(sl=True)
    mc.select(sourceGeo, targetGeo, replace=True)
    cmd = 'doWrapArgList "7" {{ "1","0","1", "2", "{}", "1", "0", "0" }}'.format(exclusiveBind)
    wrap = mm.eval(cmd)[0]
    if sel:
        mc.select(sel, replace=True)

    return wrap


def createWrapDeformer(sourceGeo, targetGeo, weightThreshold=0.0, maxDistance=1.0, exclusiveBind=True,
                       autoWeightThreshold=True, falloffMode=0, name='wrap'):
    """
    Create wrap deformer
    Ryan Roberts Michael Clavan

    :param sourceGeo: The geo that is being controlled by the wrap
    :type  sourceGeo: str

    :param targetGeo: The geo that is being wrapped to.
    :type  targetGeo: str

    :param weightThreshold: Weight threshold under which no deformation takes place
    :type  weightThreshold: double

    :param maxDistance: Distance threshold over which points on the deformed surface are not affected.
                        Use zero to turn the max distance off.
    :type  maxDistance: distance (double)

    :param exclusiveBind: Exclusive bind for weighting. If on, only weights of zero and one are assigned. If off,
                          weights are computed based on distance Only applies to mesh influence objects
    :type  exclusiveBind: bool

    :param autoWeightThreshold: Automatically compute a minumum weight cutoff such that every point on the deformed
                                surface is affected by at least one deformer point. If this attribute is set,
                                the maxDistance and weightThreshold attributes are ignored.
    :type  autoWeightThreshold: bool

    :param falloffMode: How the falloff should be applied.
                        A Volume based falloff (0) affects components based on their 3D distance from the influence point(s).
                        A Surface based falloff (1) uses the distance across the surface being deformed
    :type falloffMode: enum

    :param name: Name of wrap deformer
    :type  name: str

    :return: wrap deformer
    """
    influence = sourceGeo
    surface = targetGeo
    #     if not isinstance (influence, str):
    #         mc.error('Influence must be a string')
    #     if not isinstance (surface, str):
    #         mc.error('Surface must be a string')

    # If we're already getting shapes, pass them
    if mc.ls(influence, geometry=True):
        influenceShape = influence
        influence = mc.listRelatives(influence, p=True)[0]
    else:
        shapes = mc.listRelatives(influence, shapes=True)
        influenceShape = shapes[0]

    if mc.ls(surface, geometry=True):
        surfaceShape = surface
        surface = mc.listRelatives(surface, p=True)[0]
    else:
        shapes = mc.listRelatives(surface, shapes=True)
        surfaceShape = shapes[0]

    # create wrap deformer
    wrapData = mc.deformer(surface, type='wrap', name=name)
    wrapNode = wrapData[0]

    mc.setAttr(wrapNode + '.weightThreshold', weightThreshold)
    mc.setAttr(wrapNode + '.maxDistance', maxDistance)
    mc.setAttr(wrapNode + '.exclusiveBind', exclusiveBind)
    mc.setAttr(wrapNode + '.autoWeightThreshold', autoWeightThreshold)
    mc.setAttr(wrapNode + '.falloffMode', falloffMode)
    mc.connectAttr(surface + '.worldMatrix[0]', wrapNode + '.geomMatrix')

    # add influence
    duplicateData = mc.duplicate(influence, name=influence + 'Base')
    base = duplicateData[0]
    shapes = mc.listRelatives(base, shapes=True)
    baseShape = shapes[0]
    mc.hide(base)

    # create dropoff attr if it doesn't exist
    if not mc.attributeQuery('dropoff', n=influence, exists=True):
        mc.addAttr(influence, sn='dr', ln='dropoff', dv=4.0, min=0.0, max=20.0)
        mc.setAttr(influence + '.dr', k=True)

    # if type mesh
    if mc.nodeType(influenceShape) == 'mesh':
        # create smoothness attr if it doesn't exist
        if not mc.attributeQuery('smoothness', n=influence, exists=True):
            mc.addAttr(influence, sn='smt', ln='smoothness', dv=0.0, min=0.0)
            mc.setAttr(influence + '.smt', k=True)

        # create the inflType attr if it doesn't exist
        if not mc.attributeQuery('inflType', n=influence, exists=True):
            mc.addAttr(influence, at='short', sn='ift', ln='inflType', dv=2, min=1, max=2)

        mc.connectAttr(influenceShape + '.worldMesh', wrapNode + '.driverPoints[0]')
        mc.connectAttr(baseShape + '.worldMesh', wrapNode + '.basePoints[0]')
        mc.connectAttr(influence + '.inflType', wrapNode + '.inflType[0]')
        mc.connectAttr(influence + '.smoothness', wrapNode + '.smoothness[0]')

    # if type nurbsCurve or nurbsSurface
    if mc.nodeType(influenceShape) == 'nurbsCurve' or mc.nodeType(influenceShape) == 'nurbsSurface':
        # create the wrapSamples attr if it doesn't exist
        if not mc.attributeQuery('wrapSamples', n=influence, exists=True):
            mc.addAttr(influence, at='short', sn='wsm', ln='wrapSamples', dv=10, min=1)
            mc.setAttr(influence + '.wsm', k=True)

        mc.connectAttr(influenceShape + '.ws', wrapNode + '.driverPoints[0]')
        mc.connectAttr(baseShape + '.ws', wrapNode + '.basePoints[0]')
        mc.connectAttr(influence + '.wsm', wrapNode + '.nurbsSamples[0]')

    mc.connectAttr(influence + '.dropoff', wrapNode + '.dropoff[0]')
    # return wrapNode
    return (wrapNode)


def getWraps(geometry):
    """
    This will check the geometry to see if it has a wrap in it's history stack

    :param geometry: The mesh you want to check for a wrap
    :type geometry: str
    """
    # check the history to see if there is a wrap
    hist = mc.listHistory(geometry, pdo=True, il=2) or []
    hist = [node for node in hist if mc.nodeType(node) == "wrap"]
    return hist
