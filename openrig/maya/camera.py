"""camera functions"""

import math

import maya.cmds as mc
import maya.api.OpenMaya as om2


def getCurrentCamera():
    """Return the camera belonging to the active modelPanel."""
    panelWithFocus = mc.getPanel(wf=True)
    if mc.getPanel(to=panelWithFocus) == 'modelPanel':
        activeModelPanel = panelWithFocus
    else:
        activeModelPanel = None
    
    return mc.modelPanel(activeModelPanel, q=True, camera=True)


def getFrustum(camera):
    """Utility function to return the numerical representation of the camera
    frustum as a dict.
    
    **Frustum Data Returned**
    'nearClip' : float - near clipping plane
    'farClip': float - far clipping plane
    'aspectRatio': float - aspect ratio
    'renderFrustum': tuple - render frustrum values
    'pDist': list[float] - plane distances
    'planes': list[MVec] - normvec for right,left,bottom,top,near,far
    'incMatrixInv': MMatrix - inverse world matrix of camera
    
    :param camera: Input camera from which to calculate frustum
    :type camera: str

    :returns: frustum info dict
    :rtype: dict
    """
    frustum = {}

    # get api camera
    sel_list = om2.MSelectionList()
    sel_list.add(camera)

    cam_dg = sel_list.getDagPath(0)
    cam_fn = om2.MFnCamera(cam_dg)

    # get general attributes
    frustum['nearClip'] = cam_fn.nearClippingPlane
    frustum['farClip'] = cam_fn.farClippingPlane
    frustum['aspectRatio'] = cam_fn.aspectRatio()
    # left, right, bottom, top
    frustum['renderFrustum'] = cam_fn.getRenderingFrustum(frustum['aspectRatio'])
    frustum['pDist'] = [0.0] * 6
    frustum['incMatrixInv'] = cam_dg.inclusiveMatrixInverse()

    # build frustum plane box
    # right plane
    avec = om2.MVector(frustum['renderFrustum'][1], frustum['renderFrustum'][3], -frustum['nearClip'])
    bvec = om2.MVector(frustum['renderFrustum'][1], frustum['renderFrustum'][2], -frustum['nearClip'])
    cvec = avec ^ bvec
    frustum['planes'] = [cvec.normal()]

    # left plane
    avec = om2.MVector(frustum['renderFrustum'][0], frustum['renderFrustum'][2], -frustum['nearClip'])
    bvec = om2.MVector(frustum['renderFrustum'][0], frustum['renderFrustum'][3], -frustum['nearClip'])
    cvec = avec ^ bvec
    frustum['planes'].append(cvec.normal())

    # bottom plane
    avec = om2.MVector(frustum['renderFrustum'][1], frustum['renderFrustum'][2], -frustum['nearClip'])
    bvec = om2.MVector(frustum['renderFrustum'][0], frustum['renderFrustum'][2], -frustum['nearClip'])
    cvec = avec ^ bvec
    frustum['planes'].append(cvec.normal())

    # top plane
    avec = om2.MVector(frustum['renderFrustum'][0], frustum['renderFrustum'][3], -frustum['nearClip'])
    bvec = om2.MVector(frustum['renderFrustum'][1], frustum['renderFrustum'][3], -frustum['nearClip'])
    cvec = avec ^ bvec
    frustum['planes'].append(cvec.normal())

    # far plane
    cvec = om2.MVector(0, 0, 1)
    frustum['planes'].append(cvec)
    frustum['pDist'][4] = frustum['farClip']

    # near plane
    cvec = om2.MVector(0, 0, -1)
    frustum['planes'].append(cvec)
    frustum['pDist'][5] = frustum['nearClip']

    return frustum


def distanceFromCam(camera, node):
    """Get the distance the node is from the given camera

    :param camera: input camera
    :type camera: str

    :param node: input node
    :type node: str

    :returns: distance in current units
    :rtype: float
    """
    # get node objects
    selList = om2.MSelectionList()
    selList.add(node)
    selList.add(camera)
    node_dg = selList.getDagPath(0)
    camera_dg = selList.getDagPath(1)

    # create points from matrix
    node_worldmatrix = node_dg.inclusiveMatrix()
    node_point = om2.MPoint(node_worldmatrix[12],
                            node_worldmatrix[13],
                            node_worldmatrix[14])
    camera_worldmatrix = camera_dg.inclusiveMatrix()
    camera_point = om2.MPoint(camera_worldmatrix[12],
                              camera_worldmatrix[13],
                              camera_worldmatrix[14])

    # return distance
    return camera_point.distanceTo(node_point)

 
def objectInCamView(camera, node):
    """Determine if the given object is within the view of the given camera

    :param camera: Input camera
    :type camera: str

    :param node: Object to check camera view
    :type node: str

    :returns: If object is in camera view
    :rtype: bool
    """
    frustum = getFrustum(camera)

    # return node as api object
    selList = om2.MSelectionList()
    selList.add(node)

    node_dg = selList.getDagPath(0)
    node_fn = om2.MFnDagNode(node_dg)
    node_dg.node()

    # get object matrix and bounding box
    node_worldmatrix = node_dg.exclusiveMatrix()
    bbox = node_fn.boundingBox

    # get node bb points relative to the camera matrix
    points = []
    points.append(bbox.min * node_worldmatrix * frustum['incMatrixInv'])
    points.append(bbox.max * node_worldmatrix * frustum['incMatrixInv'])
    points.append(om2.MPoint(bbox.max.x, bbox.min.y, bbox.min.z)
                  * node_worldmatrix * frustum['incMatrixInv'])
    points.append(om2.MPoint(bbox.max.x, bbox.min.y, bbox.max.z)
                  * node_worldmatrix * frustum['incMatrixInv'])
    points.append(om2.MPoint(bbox.min.x, bbox.min.y, bbox.max.z)
                  * node_worldmatrix * frustum['incMatrixInv'])
    points.append(om2.MPoint(bbox.max.x, bbox.max.y, bbox.min.z)
                  * node_worldmatrix * frustum['incMatrixInv'])
    points.append(om2.MPoint(bbox.max.x, bbox.max.y, bbox.min.z)
                  * node_worldmatrix * frustum['incMatrixInv'])
    points.append(om2.MPoint(bbox.min.x, bbox.max.y, bbox.max.z)
                  * node_worldmatrix * frustum['incMatrixInv'])

    def _relative_to_frustrum(mesh_points):
        """Find the point location relative to camera frustum"""
        num_inside = 0

        def _relative_to_plane(plane, dist, point):
            """Find location of given point in relation to plane"""
            pvec = om2.MVector(point.x, point.y, point.z)
            val = (plane * pvec) + dist
            if val > 0.0:
                return True
            elif val < 0.0:
                return False
            return True

        planes = frustum['planes']
        pdist = frustum['pDist']

        for i in range(0, 6):
            num_behind_plane = 0
            for j in range(0, 8):
                if not _relative_to_plane(planes[i], pdist[i], mesh_points[j]):
                    num_behind_plane += 1
                if num_behind_plane == 8:
                    return False
                elif num_behind_plane == 0:
                    num_inside += 1

        if num_inside == 6:
            return True
        return True

    return _relative_to_frustrum(points)
