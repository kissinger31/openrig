import maya.cmds as mc

def softMod(point, falloffMode=mc.optionVar(q='softModFalloffMode')):
    '''
    Creates a softMod at the specified geometry point (vertex, curve point, surface point) that
    rides with the geometry.

    Valid falloffMod values:
    - 0 (volume)
    - 1 (surface)    
    
    :param point: vertex, curve point, or surface point
    :type point: str
    
    :param falloffMode: softMod falloff mode (0: volume or 1: surface)
    :type falloffMode: int
    '''
    # validate geo point
    if not mc.objExists(point):
        return
    
    # get geometry name
    geo = point.split('.')[0]
    
    # create softMod
    softMod, softModHandle = mc.softMod(geo)
    mc.setAttr(softMod+'.falloffAroundSelection', 0)
    mc.setAttr(softMod+'.falloffMode', falloffMode)
    mc.connectAttr(geo+'.worldMatrix', softMod+'.geomMatrix[0]')
    
    for attr in ['rp', 'rpt', 'sp', 'spt', 'origin']:
        mc.setAttr(softModHandle+'.'+attr, 0, 0, 0)
    mc.setAttr(softModHandle+'.v', k=False)
    mc.setAttr(softModHandle+'.displayHandle', 1)
    
    # add control attrs
    mc.addAttr(softModHandle, ln='_softModOnGeo', at='message', h=True, k=False)
    mc.addAttr(softModHandle, ln='customContextMenu', dt='string', h=True, k=False)
    mc.setAttr(softModHandle+'.customContextMenu', 'deformerOnGeoMenu', type='string')
    
    # get input geometry plug
    plug = mc.listConnections(softMod+'.input[0].inputGeometry', p=True)[0]
    
    # create nul
    nul = mc.createNode('transform', n=softModHandle+'_nul')
    mc.setAttr(nul+'.it', 0)
    mc.setAttr(nul+'.v', cb=True)
    
    # create offset
    offset = mc.createNode('transform', n=softModHandle+'_offset', p=nul)
    mc.setAttr(offset+'.v', k=False)
    
    # create offset for falloff
    offsetWorldXform = mc.createNode('transform', n=softModHandle+'_offsetWorldXform', p=nul)
    mc.setAttr(offsetWorldXform+'.io', 1)
    mc.setAttr(offsetWorldXform+'.it', 0)
    mc.connectAttr(offsetWorldXform+'.t', softMod+'.falloffCenter', f=True)
    mc.setAttr(softMod+'.falloffCenter', l=True)
    
    mc.pointConstraint(offset, offsetWorldXform)
    
    # parent and connect prebind
    mc.parent(softModHandle, offset, r=True)
    mc.connectAttr(softModHandle+'.pim', softMod+'.bindPreMatrix', f=True)

    # attach to geometry
    attachDeformerToGeo(point, geo, nul, plug)
    
    # select handle
    mc.select(softModHandle)
    
    return softMod
    

def cluster(point):
    '''
    Creates a cluster at the specified geometry point (vertex, curve point, surface point) that
    rides with the geometry.

    :param point: vertex, curve point, or surface point
    :type point: str
    '''
    # validate geo point
    if not mc.objExists(point):
        return
    
    # get geometry name
    geo = point.split('.')[0]
    
    # create cluster
    cluster, clusterHandle = mc.cluster(geo)
    mc.connectAttr(geo+'.worldMatrix', cluster+'.geomMatrix[0]')
    
    for attr in ['rp', 'rpt', 'sp', 'spt', 'origin']:
        mc.setAttr(clusterHandle+'.'+attr, 0, 0, 0)    
    mc.setAttr(clusterHandle+'.v', k=False)
    mc.setAttr(clusterHandle+'.displayHandle', 1)
    
    # add control attrs
    mc.addAttr(clusterHandle, ln='_clusterOnGeo', at='message', h=True, k=False)
    mc.addAttr(clusterHandle, ln='customContextMenu', dt='string', h=True, k=False)
    mc.setAttr(clusterHandle+'.customContextMenu', 'deformerOnGeoMenu', type='string')
        
    # get input geometry plug
    plug = mc.listConnections(cluster+'.input[0].inputGeometry', p=True)[0]
    
    # create nul
    nul = mc.createNode('transform', n=clusterHandle+'_nul')
    mc.setAttr(nul+'.it', 0)
    mc.setAttr(nul+'.v', k=False)
    
    # create offset
    offset = mc.createNode('transform', n=clusterHandle+'_offset', p=nul)
    mc.setAttr(offset+'.v', k=False)

    # parent and connect prebind    
    mc.parent(clusterHandle, offset, r=True)
    mc.connectAttr(clusterHandle+'.pim', cluster+'.bindPreMatrix', f=True)
    
    # attach to geometry
    attachDeformerToGeo(point, geo, nul, plug)

    # select handle
    mc.select(clusterHandle)
    
    return cluster
    

def attachDeformerToGeo(point, geo, nul, plug):
    '''
    Core functionality for attaching deformers to surfaces.  Used by softModOnVert() and
    clusterOnVert().

    :param point: vertex, curve point, or surface point
    :type point: str

    :param geo: name of input geometry
    :type geo: str

    :param nul: nul transform to be connected
    :type nul: str

    :param plug: input geometry connection
    :type plug: str
    
    :returns: all surface nodes created by this function.
    :rtype: list
    '''
    # get geometry type
    geoType = mc.nodeType(point)
    
    # attach to geo
    nodes = list()
    if geoType == 'mesh':
        # get edge and vert
        edge = mc.polyInfo(point, vertexToEdge=True)[0].split(':')[1].split()[0]
        vert = point.split('[')[-1].split(']')[0]
        
        # curveFromMeshEdge
        name = '%s_edge%s_curveFromMeshEdge' % (geo, edge)
        curveFromMeshEdge = mc.createNode('curveFromMeshEdge', n=name)
        nodes.append(curveFromMeshEdge)

        mc.setAttr(curveFromMeshEdge+'.edgeIndex[0]', int(edge))
        mc.connectAttr(plug, curveFromMeshEdge+'.inputMesh')
                
        # pointOnCurveInfo
        name = '%s_edge%s_vtx%s_pointOnCurveInfo' % (geo, edge, vert)
        pointOnCurveInfo = mc.createNode('pointOnCurveInfo', n=name)
        nodes.append(pointOnCurveInfo)

        mc.setAttr(pointOnCurveInfo+'.turnOnPercentage', 1)
        mc.connectAttr(curveFromMeshEdge+'.outputCurve', pointOnCurveInfo+'.inputCurve')
                
        mc.connectAttr(pointOnCurveInfo+'.result.position', nul+'.translate')
        
        # add control attrs
        mc.addAttr(pointOnCurveInfo, ln='targetVertex', at='long')
        mc.setAttr(pointOnCurveInfo+'.targetVertex', int(vert))
        mc.addAttr(pointOnCurveInfo, ln='targetGeometry', dt='string')
        mc.setAttr(pointOnCurveInfo+'.targetGeometry', geo, type='string')
        
        # make sure the parameter places nul at vertex postion
        nul_pos = mc.xform(nul, q=True, ws=True, t=True)
        vert_pos = mc.xform(point, q=True, ws=True, t=True)
        if not all(isclose(n, v, rel_tol=1e-05) for n, v in zip(nul_pos, vert_pos)):
            mc.setAttr(pointOnCurveInfo+'.parameter', 1)

        # normalConstraint
        constraint = mc.createNode('normalConstraint', n=nul+'_normalConstraint', p=nul)
        nodes.append(constraint)

        mc.setAttr(constraint+'.io', 1)
        mc.setAttr(constraint+'.aimVector', 1, 0, 0)
        mc.setAttr(constraint+'.upVector', 0, 1 , 0)
        mc.setAttr(constraint+'.lockOutput', 1)
        mc.setAttr(constraint+'.enableRestPosition', 0)
                
        mc.connectAttr(plug, constraint+'.target[0].targetGeometry')
        mc.connectAttr(pointOnCurveInfo+'.tangent', constraint+'.worldUpVector')
        
        mc.connectAttr(nul+'.parentInverseMatrix', constraint+'.constraintParentInverseMatrix', f=True)
        mc.connectAttr(nul+'.t', constraint+'.constraintTranslate', f=True)
        mc.connectAttr(nul+'.rp', constraint+'.constraintRotatePivot', f=True)
        mc.connectAttr(nul+'.rpt', constraint+'.constraintRotateTranslate', f=True)
        mc.connectAttr(nul+'.ro', constraint+'.constraintRotateOrder', f=True)
        
        mc.connectAttr(constraint+'.constraintRotateX', nul+'.rx', f=True)
        mc.connectAttr(constraint+'.constraintRotateY', nul+'.ry', f=True)
        mc.connectAttr(constraint+'.constraintRotateZ', nul+'.rz', f=True)
        
    elif geoType == 'nurbsCurve':
        # get parameter
        parameter = float(point.split('[')[-1].split(']')[0])
        
        # pointOnCurveInfo
        name = '%s_%s_pointOnCurveInfo' % (geo, str(parameter).replace('.', '_'))
        pointOnCurveInfo = mc.createNode('pointOnCurveInfo', n=name)
        nodes.append(pointOnCurveInfo)

        mc.setAttr(pointOnCurveInfo+'.parameter', parameter)
        mc.connectAttr(plug, pointOnCurveInfo+'.inputCurve')
                
        mc.connectAttr(pointOnCurveInfo+'.result.position', nul+'.translate')
        
        # add control attrs        
        mc.addAttr(pointOnCurveInfo, ln='targetGeometry', dt='string')
        mc.setAttr(pointOnCurveInfo+'.targetGeometry', geo, type='string')
        
        # buildRotation
        if not mc.pluginInfo('buildRotationNode', q=True, loaded=True):
            mc.loadPlugin('buildRotationNode')

        buildRotation = mc.createNode('buildRotation', n=nul+'_buildRotation')
        nodes.append(buildRotation)

        mc.connectAttr(pointOnCurveInfo+'.normal', buildRotation+'.up', f=True)
        mc.connectAttr(pointOnCurveInfo+'.tangent', buildRotation+'.forward', f=True)
        mc.connectAttr(nul+'.ro', buildRotation+'.rotateOrder', f=True)
        mc.connectAttr(buildRotation+'.rotate', nul+'.r', f=True)
        
    elif geoType == 'nurbsSurface':
        # get parameters
        u, v = [float(p) for p in point.split('.uv')[1].replace('][', ' ').replace('[', '').replace(']', '').split()]
        
        # pointOnSurfaceInfo
        name = '%s_%s_%s_pointOnSurfaceInfo' % (geo, str(u).replace('.', '_'), str(v).replace('.', '_'))
        pointOnSurfaceInfo = mc.createNode('pointOnSurfaceInfo', n=name)
        nodes.append(pointOnSurfaceInfo)

        mc.setAttr(pointOnSurfaceInfo+'.parameterU', u)
        mc.setAttr(pointOnSurfaceInfo+'.parameterV', v)
        mc.connectAttr(plug, pointOnSurfaceInfo+'.inputSurface')
                
        mc.connectAttr(pointOnSurfaceInfo+'.result.position', nul+'.translate')
        
        # add control attrs
        mc.addAttr(pointOnSurfaceInfo, ln='targetGeometry', dt='string')
        mc.setAttr(pointOnSurfaceInfo+'.targetGeometry', geo, type='string')
        
        # normalConstraint
        constraint = mc.createNode('normalConstraint', n=nul+'_normalConstraint', p=nul)
        nodes.append(constraint)

        mc.setAttr(constraint+'.io', 1)
        mc.setAttr(constraint+'.aimVector', 1, 0, 0)
        mc.setAttr(constraint+'.upVector', 0, 1 , 0)
        mc.setAttr(constraint+'.lockOutput', 1)
        mc.setAttr(constraint+'.enableRestPosition', 0)
                
        mc.connectAttr(plug, constraint+'.target[0].targetGeometry')
        mc.connectAttr(pointOnSurfaceInfo+'.tangentU', constraint+'.worldUpVector')
        
        mc.connectAttr(nul+'.parentInverseMatrix', constraint+'.constraintParentInverseMatrix', f=True)
        mc.connectAttr(nul+'.t', constraint+'.constraintTranslate', f=True)
        mc.connectAttr(nul+'.rp', constraint+'.constraintRotatePivot', f=True)
        mc.connectAttr(nul+'.rpt', constraint+'.constraintRotateTranslate', f=True)
        mc.connectAttr(nul+'.ro', constraint+'.constraintRotateOrder', f=True)
        
        mc.connectAttr(constraint+'.constraintRotateX', nul+'.rx', f=True)
        mc.connectAttr(constraint+'.constraintRotateY', nul+'.ry', f=True)
        mc.connectAttr(constraint+'.constraintRotateZ', nul+'.rz', f=True)
        
    else:
        mc.warning('Cannot attach deformer to geometry "%s" of type "%s"' % (geo, geoType))
        return    
    
    return nodes


def isclose(a, b, rel_tol=1e-09, abs_tol=0.0):
    return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)