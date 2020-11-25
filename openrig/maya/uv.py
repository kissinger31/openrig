"""UV utilities."""

from collections import defaultdict
import operator
import itertools
import math

import maya.cmds as mc
import maya.api.OpenMaya as om2

from openrig.maya.modlib import mesh


def space(uvList, axis, useSelectionOrder=False, spacing=0.2):
    """Evenly spaces UVs on the given axis.

    VaLid axis values:
    - 'u'
    - 'v'

    :param uvList: list of UVs
    :type uvList: list

    :param axis: axis to align to ('u' or 'v')
    :type axis: str

    :param useSelectionOrder: whether to use original selection order
    :type useSelectionOrder: bool
    
    :param spacing: how much space between UV shells
    :type spacing: float
    """
    # get UVs
    uvList = mc.ls(uvList, fl=True)
    if len(uvList) < 2:
        return

    if not useSelectionOrder or not mc.selectPref(q=True, tso=True):
        uvList = getOrderOnAxis(uvList, axis)

    # get step value
    start_pos = mc.polyEditUV(uvList[0], q=True, u=True, v=True)
    value = start_pos[0] if axis is 'u' else start_pos[1]
    step = value + spacing

    # space
    for uv in uvList[1:]:
        # get position
        pos = mc.polyEditUV(uv, q=True, u=True, v=True)

        # get values
        uValue = step - pos[0] if axis is 'u' else 0.0
        vValue = step - pos[1] if axis is 'v' else 0.0

        # move
        mc.polyEditUV(uv, u=uValue, v=vValue)

        step += spacing


def distribute(uvList, axis, useSelectionOrder=False):
    """Evenly distributes UVs in the given axis.

    VaLid axis values:
    - 'u'
    - 'v'

    :param uvList: list of UVs
    :type uvList: list

    :param axis: axis to align to ('u' or 'v')
    :type axis: str

    :param useSelectionOrder: whether to use original selection order
    :type useSelectionOrder: bool
    """
    # get UVs
    uvList = mc.ls(uvList, fl=True)
    if len(uvList) < 3: return

    if not useSelectionOrder or not mc.selectPref(q=True, tso=True):
        uvList = getOrderOnAxis(uvList, axis)

    # get first and last UV positions
    pos1 = mc.polyEditUV(uvList[0], q=True, u=True, v=True)
    pos2 = mc.polyEditUV(uvList[-1], q=True, u=True, v=True)

    # get distance between first and last points
    distance = float()
    if axis is 'u':
        distance = abs(pos1[0] - pos2[0])
    if axis is 'v':
        distance = abs(pos1[1] - pos2[1])

    # get step value
    stepSize = distance / (len(uvList) - 1)
    value = pos1[0] if axis is 'u' else pos1[1]
    step = value + stepSize

    # distribute
    for uv in uvList[1:-1]:
        # get position
        pos = mc.polyEditUV(uv, q=True, u=True, v=True)

        # get values
        uValue = step - pos[0] if axis is 'u' else 0.0
        vValue = step - pos[1] if axis is 'v' else 0.0

        # move
        mc.polyEditUV(uv, u=uValue, v=vValue)

        step += stepSize


def alignShells(uvList, direction):
    """Align UV shells in given direction.

    Valid directions on U:
    - left
    - centerU
    - right

    Valid directions on V:
    - top
    - centerV
    - bottom

    :param uvList: list of UVs to expand to shells
    :type uvList: list

    :param direction: align (left, centerU, right, top, centerV, bottom)
    :type direction: str
    """
    # get shells
    shells = getShells(uvList)
    if len(shells) < 2:
        return

    # get bounding box for all shells
    allShells = list(itertools.chain(*shells))
    bb = getBoundingBox(allShells)

    # align
    for shell in shells:
        # get shell bounding box
        shell_bb = getBoundingBox(shell)

        # get values
        if direction in ['top', 'centerV', 'bottom']:
            uValue = 0.0
        if direction in ['left', 'centerU', 'right']:
            vValue = 0.0

        if direction is 'top':
            vValue = bb['vmax'] - shell_bb['vmax']
        if direction is 'centerV':
            vValue = bb['vcenter'] - shell_bb['vcenter']
        if direction is 'bottom':
            vValue = bb['vmin'] - shell_bb['vmin']

        if direction is 'left':
            uValue = bb['umin'] - shell_bb['umin']
        if direction is 'centerU':
            uValue = bb['ucenter'] - shell_bb['ucenter']
        if direction is 'right':
            uValue = bb['umax'] - shell_bb['umax']

        # move
        mc.polyEditUV(shell, u=uValue, v=vValue)


def alignShellToAxis(uvList, axis):
    """Given a set of UVs the shell belonging to the selection is rotated to
    align to given axis.

    Valid axis values:
    - 'u'
    - 'v'

    :param uvList: a list of exactly 2 UVs
    :type uvList: list | tuple

    :param axis: axis to align to ('u' or 'v')
    :type axis: str
    """
    # validate UVs
    if not isinstance(uvList, list or tuple):
        raise StandardError('Provide a UV list or tuple.')
    if len(uvList) != 2:
        mc.warning('Only using first 2 values in the given UV list.')
        uvList = uvList[:2]

    # get positions
    uv1 = mc.polyEditUV(uvList[0], query=True, uValue=True, vValue=True)
    uv2 = mc.polyEditUV(uvList[1], query=True, uValue=True, vValue=True)

    # punt on invalid requests
    if uv1[0] == uv2[0] and axis == 'v':
        return
    if uv1[1] == uv2[1] and axis == 'u':
        return

    # get order and quadrant
    quad = 1
    if uv1[0] > uv2[0]:
        uv1, uv2 = uv2, uv1
    if uv2[1] < uv1[1]:
        quad = 2

    # run calculation
    atan = math.atan2((uv1[0] - uv2[0]), (uv1[1] - uv2[1]))
    angle = (math.degrees(abs(atan) % (.5 * math.pi)))

    # convert angle based on inputs
    if quad == 1 and axis == 'v':
        angle = angle - 90
    if quad == 2 and axis == 'u':
        angle = angle - 90
    elif angle > 45:
        angle = angle - 90
    if uv1[1] == uv2[1] and axis == 'v':
        angle = 90
    if uv1[0] == uv2[0] and axis == 'u':
        angle = -90

    # get pivot
    pivotU = (uv1[0] + uv2[0]) / 2
    pivotV = (uv1[1] + uv2[1]) / 2

    # get shells
    shells = list(itertools.chain(*getShells(uvList)))

    # move uvs
    mc.polyEditUV(shells, pivotU=pivotU, pivotV=pivotV, rotation=1, angle=-angle)


def distributeShells(uvList, axis, useCenters=False, useSelectionOrder=False):
    """Distribute UV shells in given axis.  By default distribution is based on
    each shell's width. Set "useCenters" True to distribute based on the shells
    centers.

    Valid axis values:
    - 'u'
    - 'v'

    :param uvList: list of UVs to expand to shells
    :type uvList: list

    :param axis: distribute axis (u, v)
    :type axis: str

    :param useCenters: wheather to distribute based on shell centers (False)
    :type useCenters: bool

    :param useSelectionOrder: whether to use original selection order
    :type useSelectionOrder: bool
    """
    # get shells
    orderOnAxis = None if useSelectionOrder else axis
    shells = getShells(uvList, orderOnAxis=orderOnAxis)
    if len(shells) < 3:
        return

    # get bounding boxes for first and last shells
    bb1 = getBoundingBox(shells[0])
    bb2 = getBoundingBox(shells[-1])

    # distribute on centers
    if useCenters:
        # get distance between first and last shell centers
        distance = float()
        if axis is 'u':
            distance = abs(bb2['ucenter'] - bb1['ucenter'])
        if axis is 'v':
            distance = abs(bb2['vcenter'] - bb1['vcenter'])

        # get step values
        stepSize = distance / (len(shells) - 1)
        centerValue = bb1['ucenter'] if axis is 'u' else bb1['vcenter']
        step = centerValue + stepSize

        # distribute
        for shell in shells[1:-1]:
            # get shell bounding box
            shell_bb = getBoundingBox(shell)

            # get values
            uValue = step - shell_bb['ucenter'] if axis is 'u' else 0.0
            vValue = step - shell_bb['vcenter'] if axis is 'v' else 0.0

            # move
            mc.polyEditUV(shell, u=uValue, v=vValue)

            step += stepSize

    # distribute by widths
    else:
        # get distance between first and last shells
        distance = float()
        if axis is 'u':
            distance = abs(bb2['umin'] - bb1['umax'])
        if axis is 'v':
            distance = abs(bb2['vmin'] - bb1['vmax'])

        # get total dimension (width or height) of intermediate shells
        shellsDimension = float()
        dimension = 'width' if axis is 'u' else 'height'
        for shell in shells[1:-1]:
            shellsDimension += getBoundingBox(shell)[dimension]

        # get step values
        stepSize = (distance - shellsDimension) / (len(shells) - 1)
        maxValue = bb1['umax'] if axis is 'u' else bb1['vmax']
        step = maxValue + stepSize

        # distribute
        for shell in shells[1:-1]:
            # get shell bounding box
            shell_bb = getBoundingBox(shell)

            # get values
            uValue = step - shell_bb['umin'] if axis is 'u' else 0.0
            vValue = step - shell_bb['vmin'] if axis is 'v' else 0.0

            # move
            mc.polyEditUV(shell, u=uValue, v=vValue)

            step += shell_bb[dimension] + stepSize


def spaceShells(uvList, axis, useCenters=False, useSelectionOrder=False,
                spacing=0.2):
    """Adds spacing between given UV shells.  In the 'u' axis shells are spaced
    from left to right.  In the 'v' axis they are spaced from bottom to top.

    Valid axis values:
    - 'u'
    - 'v'

    :param uvList: list of UVs to expand to shells
    :type uvList: list

    :param axis: distribute axis (u, v)
    :type axis: str

    :param useCenters: whether to distribute based on shell centers (False)
    :type useCenters: bool

    :param useSelectionOrder: whether to use original selection order
    :type useSelectionOrder: bool

    :param spacing: how much space to add between shells
    :type spacing: float
    """
    # get shells
    orderOnAxis = None if useSelectionOrder else axis
    shells = getShells(uvList, orderOnAxis=orderOnAxis)
    if len(shells) < 2: return

    # get bounding box for first shell
    bb1 = getBoundingBox(shells[0])

    # space on centers
    if useCenters:
        # get step values
        centerValue = bb1['ucenter'] if axis is 'u' else bb1['vcenter']
        step = centerValue + spacing

        # space
        for shell in shells[1:]:
            # get shell bounding box
            shell_bb = getBoundingBox(shell)

            # get values
            uValue = step - shell_bb['ucenter'] if axis is 'u' else 0.0
            vValue = step - shell_bb['vcenter'] if axis is 'v' else 0.0

            # move
            mc.polyEditUV(shell, u=uValue, v=vValue)

            step += spacing

    # space by width
    else:
        # get step values
        maxValue = bb1['umax'] if axis is 'u' else bb1['vmax']
        step = maxValue + spacing

        # distribute
        for shell in shells[1:]:
            # get shell bounding box
            shell_bb = getBoundingBox(shell)

            # get values
            uValue = step - shell_bb['umin'] if axis is 'u' else 0.0
            vValue = step - shell_bb['vmin'] if axis is 'v' else 0.0

            # move
            mc.polyEditUV(shell, u=uValue, v=vValue)

            dimension = shell_bb['width'] if axis is 'u' else shell_bb['height']
            step += dimension + spacing


def getOrderOnAxis(uvList, axis=True):
    """Returns list of UVs in order according to axis. Order can be
    unpredictable UVs are coincident.

    :param uvList: list of UVs
    :type uvList: list

    :param axis: axis to align to ('u' or 'v')
    :type axis: str

    :returns: list of UVs in order along given axis
    :rtype: list
    """
    # get position values
    uv_order = list()
    for uv in uvList:
        pos = mc.polyEditUV(uv, q=True, u=True, v=True)
        value = pos[0] if axis is 'u' else pos[1]
        uv_order.append((value, uv))

    # sort
    uv_order.sort(key=lambda tup: tup[0])
    uvList = [uv for value, uv in uv_order]

    return uvList


def getBoundingBox(uvList):
    """Return a bounding box dictionary for any arbitrary list of input UVs.

    bb = {'umin', 'umax',
          'vmin', 'vmax',
          'width', 'height',
          'ucenter', 'vcenter'}

    :param uvList: input UVs list
    :type uvList: list[str]

    :returns: bounding box list
    :rtype: dict
    """
    # create box list as [umin, vmin, umax, vmax, w, h, ucenter, vcenter]
    bb = {'umin': 1e30, 'vmin': 1e30, 'umax': -1e30, 'vmax': -1e30,
          'width': 0.0, 'height': 0.0, 'ucenter': 0.0, 'vcenter': 0.0}

    # add UVs to list
    uv_list = om2.MSelectionList()
    [uv_list.add(uv) for uv in mc.ls(uvList, flatten=True)]

    # iterator
    uv_iter = om2.MItSelectionList(uv_list)

    # iterate through uv's to create box
    while not uv_iter.isDone():
        # get components
        uv_dagcomp = uv_iter.getComponent()
        compfn = om2.MFnSingleIndexedComponent(uv_dagcomp[1])
        meshfn = om2.MFnMesh(uv_dagcomp[0])

        ids = compfn.getElements()

        # test bounding box
        for i in range(len(ids)):
            uvpos = meshfn.getUV(ids[i])
            u, v = uvpos[0], uvpos[1]

            # expand box
            if u < bb['umin']: bb['umin'] = u
            if v < bb['vmin']: bb['vmin'] = v
            if u > bb['umax']: bb['umax'] = u
            if v > bb['vmax']: bb['vmax'] = v

        uv_iter.next()

    # calc other values
    bb['width'] = bb['umax'] - bb['umin']
    bb['height'] = bb['vmax'] - bb['vmin']
    bb['ucenter'] = (bb['width'] / 2) + bb['umin']
    bb['vcenter'] = (bb['height'] / 2) + bb['vmin']

    return bb


def getShells(uvList, orderOnAxis=None, uvSet='map1'):
    """Returns list of shell UVs ordered either by the order they were given or
    by the given axis.

    If orderOnAxis is None (default) shells will be returned in given order. If
    'u' or 'v' is specified it will return the shells from left to right for
    'u' and bottom to top for 'v'.

    Valid orderOnAxis values:
    - None
    - 'u'
    - 'v'

    :param uvList: list of UVs
    :type uvList: list

    :param orderOnAxis: whether to order shells by 'u' or 'v' (default None)
    :type orderOnAxis: str | None

    :returns: a list of UV lists for each shell.
    :rtype: list
    """
    # flatten UV list
    uvList = set(mc.ls(uvList, fl=True))

    # get UVs per mesh
    meshUVs = set(((uv.split('.')[0], int(uv.split('[')[-1].split(']')[0])) for uv in uvList))

    # get shell IDs
    meshes = list(set([mesh for mesh, uv in meshUVs]))
    shellsIDs = getShellsIDs(meshes, uvSet)

    # get shells
    shells = list()
    shellNames = list()
    for mesh, uv in meshUVs:
        for shell in shellsIDs[mesh]:
            if uv in shellsIDs[mesh][shell]:
                shellName = mesh + '_' + str(shell)
                if not shellName in shellNames:
                    shellNames.append(shellName)
                    shellUVs = [mesh + '.map[%s]' % str(i) for i in shellsIDs[mesh][shell]]
                    shells.append(shellUVs)

    # order shells
    if orderOnAxis is 'u' or orderOnAxis is 'v':
        shell_order = list()
        for shell in shells:
            shell_bb = getBoundingBox(shell)
            minValue = shell_bb['umin'] if orderOnAxis is 'u' else shell_bb['vmin']
            shell_order.append((minValue, shell))

        # sort
        shell_order.sort(key=lambda tup: tup[0])
        shells = [shell for minValue, shell in shell_order]

    return shells


def getShellsIDs(meshes, uvSet='map1'):
    """Returns UV shell memberships for given meshes.

    Returned dictionary follows this format.
    {mesh: {shellID: set(uv, uv, uv, ...), shellID: ...}, mesh: ...}

    :param meshes: mesh(es) to find shells for
    :type meshes: list | str

    :param uvSet: uv set name (default "map1")
    :type uvSet: str

    :returns: dictionary of mesh names and shells dictionary
    :rtype: dict
    """
    # get meshes list
    if not isinstance(meshes, set):
        if not isinstance(meshes, list):
            meshes = [meshes]
        meshes = set(meshes)
    
    # get all mesh shells
    meshShells = dict()

    # build mesh list
    selectionList = om2.MSelectionList()
    [selectionList.add(mesh) for mesh in meshes]
    selectionListIter = om2.MItSelectionList(selectionList, om2.MFn.kMesh)

    # get shells
    while not selectionListIter.isDone():
        # get shell data
        dagPath = selectionListIter.getDagPath()
        shapeFn = om2.MFnMesh(dagPath)
        shellData = shapeFn.getUvShellsIds(uvSet=uvSet)

        # add to shells dictionary
        shells = dict()
        for s in set(shellData[1]):
            shells[s] = set([i for i, uv in enumerate(shellData[1]) if uv == s])

        # add to meshes dictionary
        name = selectionListIter.getStrings()[0]
        meshShells[name] = shells

        selectionListIter.next()

    return meshShells


def getShellBorder(uvList):
    """Return a list of the uv borders

    :param uvList: list of uv's making up a single uv shell
    :type uvList: list[str]

    :returns: list of border uvs
    :rtype: list[str]
    """
    # flatten UV list
    uvList = mc.ls(uvList, fl=True)

    uvVerts = mc.ls(mc.polyListComponentConversion(uvList, toVertex=True), flatten=True)
    uvVertIndices = [x.split('.')[1][4:-1] for x in uvVerts]

    # build mesh list
    selectionList = om2.MSelectionList()
    selectionList.add(uvList[0].split('.')[0])
    meshDag = selectionList.getDagPath(0)

    # component iter
    comps = selectionList.getComponent(0)
    vertIter = om2.MItMeshVertex(comps[0], comps[1])

    borderVerts = list()
    # iterate through verts in uv shell
    for vert in uvVertIndices:
        # get vertex UV indices
        vertIter.setIndex(int(vert))
        vertUVs = [x for x in vertIter.getUVIndices()]

        if not len(set(vertUVs)) == 1:
            borderVerts.append('{0}.vtx[{1}]'.format(uvList[0].split('.')[0], vert))

    return [x for x in mc.ls(mc.polyListComponentConversion(borderVerts, toUV=True), flatten=True) if x in uvList]


def snapSelectedBorder(uvList, unfold=False):
    """Snap the selected border UVs to their corresponding uv and weld

    :param uvList: border uvs to snap
    :type uvList: list
    """
    # ensure list is flattened
    inUVs = mc.ls(mc.polyListComponentConversion(uvList, toUV=True), flatten=True)

    # get adjacent border
    allUVs = mc.ls(
        mc.polyListComponentConversion(
            mc.polyListComponentConversion(
                mc.polyListComponentConversion(inUVs, toVertex=True),
                toEdge=True, internal=True),
            toUV=True),
        flatten=True)
    pairUVs = [uv for uv in allUVs if uv not in inUVs]

    # perform snap
    for uv in inUVs:
        # get adjacent uv
        adjUV = [x for x in mc.ls(mc.polyListComponentConversion(
            mc.polyListComponentConversion(uv, toVertex=True), toUV=True), flatten=True)
            if x not in uv][0]
        # snap
        pos = mc.polyEditUV(adjUV, query=True, uValue=True, vValue=True)
        mc.polyEditUV(uv, relative=False, uValue=pos[0], vValue=pos[1])

    if unfold:
        # shells = list(itertools.chain(*getShells(inUVs)))
        shell = getShells(inUVs)[0]
        shell = [x for x in shell if x not in inUVs]
        mc.select(shell)
        # unfold doesn't hold non selected uv's very well, look for different solution
        mc.UnfoldUV(shell, unfold=True, pack=False, iterations=1,
                    triangleflip=True, mapsize=4096, roomspace=2)

    # merge
    mc.polyMergeUV(inUVs, pairUVs, distance=0.001)


def getAngleBetween(uvA, uvB):
    """Utility to return the angle between 2 uv's

    :param uvA: uv
    :type uvA: str

    :param uvB: uv
    :type uvB: str

    :returns: angle between input uvs
    :rtype: float
    """
    posA = mc.polyEditUV(uvA, query=True, uValue=True, vValue=True)
    posB = mc.polyEditUV(uvB, query=True, uValue=True, vValue=True)

    if posA[0] > posB[0]:
        posA, posB = posB, posA

    return math.atan2((posA[0] - posB[0]), (posA[1] - posB[1]))


def getDistanceBetween(uvA, uvB):
    """Utility to return the distance between 2 uv's

    :param uvA: uv
    :type uvA: str

    :param uvB: uv
    :type uvB: str

    :returns: distance between input uvs
    :rtype: float
    """
    posA = mc.polyEditUV(uvA, query=True, uValue=True, vValue=True)
    posB = mc.polyEditUV(uvB, query=True, uValue=True, vValue=True)

    return math.sqrt(math.pow(posB[0] - posA[0], 2) + math.pow(posB[1] - posA[1], 2))


def getLongContigEdge(uvList, angle=0.001):
    """Given a list UVs, return the longest contiguous edge within the
    specified tolerance.

    THIS IS A WORK IN PROGRESS FUNC

    :param uvList: list of uv's, ideally border uvs
    :type uvList: list[str]

    :param angle: tolerance of a single edge
    :type angle: float

    :returns: angle of longest edge
    :rtype: float
    """
    # flatten input
    uvList = mc.ls(uvList, flatten=True)
    # get all edges
    edgeList = mc.ls(mc.polyListComponentConversion(
        mc.polyListComponentConversion(uvList, toVertex=True), toEdge=True, internal=True), flatten=True)

    edgeInfo = dict()
    for edge in edgeList:
        # get edge uv's
        edgeUV = mc.ls(mc.polyListComponentConversion(edge, toUV=True), flatten=True)
        for a, b in itertools.combinations(edgeUV, 2):
            edgeInfo[edge + '_' + a + '_' +
                     b] = [getAngleBetween(a, b), getDistanceBetween(a, b), edge, a, b]

    # process edge info
    # group edges by angle
    angleGroups = defaultdict(list)
    for key, value in sorted(edgeInfo.iteritems()):
        angleGroups[value[0]].append(key)

    totalDistances = {}
    # get total distances of grouped angles
    for key, value in angleGroups.iteritems():
        distance = 0.0
        for edge in value:
            distance = distance + edgeInfo[edge][1]
        totalDistances[key] = distance

    # get largest edge group
    longestDist = max(totalDistances.iteritems(), key=operator.itemgetter(1))[0]

    return math.degrees(longestDist)


def layoutHardSurface(meshList, angle=45, align=False, unfold=False, layout=False, unfold3d=False, layout3d=False):
    """Utility script to break up a hard surface object and create projections
    based on a given angle

    :param meshList: list of input mesh's to perform on
    :type meshList: str

    :param angle: angle to perform breakup
    :type angle: int

    :param align: align longest edge to axis - UNFINISHED FEATURE, DOES NOTHING
    :type align: bool

    :param unfold: unfold uv shell using Maya legacy unfold
    :type unfold: bool

    :param layout: layout shells using maya legacy polyMultiLayoutUV
    :type layout: bool

    :param layout3d: layout shells using new Unfold3d layout tool
    :type layout3d: bool

    :param unfold3d: unfold shells using Unfol3d algorithm
    :type unfold3d: bool
    """
    for obj in meshList:
        # get area of all faces
        faceArea = mesh.getMeshFaceArea(obj)
        allFaces = faceArea.keys()

        # run through each mesh in list and split to uv's based on geometry edge angle
        while len(allFaces) > 0:
            # start with largest face
            projFaces = [max(faceArea.iterkeys(), key=(lambda key: faceArea[key]))]

            def _getConnectedProjFaces(inFace, projFaces, angle):
                """Return all connected faces within angle tolerance"""
                addedFaces = list()
                # get connected faces
                connected_faces = mesh.getConnectedFaces(inFace)
                for face in connected_faces:
                    if mesh.getAngleBetweenFaces(inFace, face) < angle:
                        addedFaces.append(face)

                addedFaces = [x for x in addedFaces if x not in projFaces]
                projFaces += addedFaces
                return addedFaces

            # add new faces to projection
            counter = 0
            inFaces = projFaces
            while len(inFaces) > 0:
                for inFace in inFaces:
                    inFaces = _getConnectedProjFaces(inFace, projFaces, angle)
                continue

            # remove projected faces from dict
            allFaces = [x for x in allFaces if x not in projFaces]
            for k in projFaces:
                faceArea.pop(k, None)

            # make projection
            mc.select(projFaces)
            mc.polyProjection(keepImageRatio=True, mapDirection='b')

            # standard unfold
            if unfold:
                mc.unfold(obj)

            # standard layout
            if layout:
                mc.polyMultiLayoutUV(obj, flipReversed=True, layout=2, layoutMethod=1,
                                     prescale=2, scale=1, rotateForBestFit=1)

        mc.select(clear=True)
        # unfold, catch non-manifold error
        if unfold3d:
            try:
                mc.u3dUnfold(obj, borderintersection=False, iterations=1, mapsize=4096,
                             pack=False, roomspace=2, triangleflip=False)
            except:
                mc.warning('Non-manifold uvs present, skipping Unfold3d.')

        # rotate shells - UNFINISHED FEATURE, LOW TIME INVESTMENT RETURN
        # if align:
        #     # get all shells
        #     shells = getShells(mc.polyListComponentConversion(obj, toUV=True))

        #     # for each shell get longest contiguous edge
        #     for shell in shells:
        #         # get border uvs
        #         shellBorder = getShellBorder(shell)

        #         # get angle of longest contig edge
        #         longEdgeAngle = getLongContigEdge(shellBorder)

        #         # rotate shell with align to axis
        #         diffAngle = abs(longEdgeAngle)
        #         rotAngle = 0
        #         if diffAngle <= 90:
        #             rotAngle = 90 - diffAngle
        #         if diffAngle > 90 and diffAngle < 180:
        #             rotAngle = diffAngle - 90
        #         if diffAngle >= 180 and diffAngle < 270:
        #             rotAngle = 180 - diffAngle
        #         if diffAngle >=270:
        #             rotAngle = diffAngle - 180

        #         print diffAngle, rotAngle

        #         bb = getBoundingBox(shell)
                # mc.polyEditUV(shell, pivotU=bb['ucenter'], pivotV=bb['vcenter'], angle=rotAngle)

        # layout uvs, catch non-manifold error
        if layout3d:
            try:
                mc.u3dLayout(obj, resolution=64, packBox=[0, 1, 0, 1], preScaleMode=3)
            except:
                mc.warning('Non-manifold uvs present, skipping Unfold3d Layout.')

    mc.select(meshList)


def layoutUVGrid(objs, tileSpace=1, padding=0.003, u=1, v=1, udim=1001, resize=False, resizeTiles=1):
    """Layout a group of selected objects in a grid pattern.

    :param objs: list of selected objects
    :type objs: list

    :param tileSpace: specify using the entire tile or half the tile
    :type tileSpace: float

    :param padding: space between UV shell groups
    :type padding: float

    :param u: specify starting u
    :type u: int

    :param v: specify starting v
    :type v:  int

    :param udim: specify starting tile as udim number
    :type udim: int

    :param resize: should shells be resized to fit a grid within the specified
                   number of tiles
    :type resize: bool

    :param resizeTiles: number of tiles to fit the resized shells into
    :type resizeTiles: int
    """

    # check for UDIM input and convert if necessary
    if udim > 1001:
        uv = convertUDIMtoUV(udim)

        u = uv[0]
        v = uv[1]+1

    # flatten list
    objList = mc.ls(objs, flatten=True)
    objNum = len(objList)

    # determine scale factor and numbering on first object to limit repeat calc
    # convert to UV
    selUV = mc.polyListComponentConversion(objList[0], toUV=True)

    # get bbox
    bbox = mc.polyEvaluate(selUV, boundingBoxComponent2d=True)
    bboxX = bbox[0][1] - bbox[0][0]
    bboxY = bbox[1][1] - bbox[1][0]

    if resize is True:
        # determine optimal size from shell # and pre-scale
        numPerTile = int(math.ceil(math.ceil(float(objNum) / float(resizeTiles))))
        sizeRatio = bboxY / bboxX

        sRoot = math.floor(math.sqrt(numPerTile / tileSpace))
        xNum = math.floor(sRoot * sizeRatio * tileSpace)
        yNum = math.ceil(numPerTile / xNum)

        # test theory on numbering
        while (tileSpace - (xNum * bboxX)) > bboxX and (1 - (yNum * bboxY)) < bboxY:
            xNum += 1
            yNum = math.ceil(numPerTile / xNum)

        scaleF = (tileSpace - ((padding * 2) * xNum)) / (xNum * bboxX)
        scaleY = (1 - ((padding * 2) * yNum)) / (yNum * bboxY)

        # check for largest scale
        if scaleF > scaleY:
            scaleF = scaleY

        # ensure under 1 to compensate for rounding and relative padding
        print (((bboxX * scaleF) + (padding * 2)) * xNum)

    else:
        xNum = math.floor(tileSpace / (bboxX + (padding * 2)))
        yNum = math.floor(1 / (bboxY + (padding * 2)))
        scaleF = 1

    # counters
    countU=0
    countV=1

    for obj in objList:
        # convert to UV
        selUV = mc.polyListComponentConversion(obj, toUV=True)

        if scaleF != 1:
            # prescale based on factor
            mc.polyEditUV(selUV, scaleU=scaleF, scaleV=scaleF)

        # recalc bbox
        # get bbox
        bbox = mc.polyEvaluate(selUV, boundingBoxComponent2d=True)
        bboxX = bbox[0][1] - bbox[0][0] + (padding * 2)
        bboxY = bbox[1][1] - bbox[1][0] + (padding * 2)

        # move to 0
        mc.polyEditUV(selUV, uValue=bbox[0][0] * -1 + padding, vValue=bbox[1][0] * -1 + padding)

        # move to position
        bbox = mc.polyEvaluate(selUV, boundingBoxComponent2d=True)
        mc.polyEditUV(selUV, uValue=abs(tileSpace-1) + bboxX * countU + u-1, vValue=1 - bboxY * countV + v-1)

        countU += 1
        if countU >= xNum:
            countV += 1
            countU = 0
        if countV > yNum:
            countU = 0
            countV = 1
            u += 1
            if u > 9:
                u = 0
                v += 1


def convertUDIMtoUV(udim=1001):
    """Helper script to convert UDIM to Maya U and V coordinates

    :param udim: UDIM tile number
    :type udim: int
    """

    # ensure proper udim number
    if udim < 1000 or udim > 9999:
        mc.error('Input is not a proper UDIM tile number')

    #set up default coordinates
    uv = [0,0]

    uv[0] = (udim // 1)%10
    if uv[0] == 0:
        uv[0] += 10
    uv[1] = (int(round((udim-1000),-1))) // 10

    return uv
