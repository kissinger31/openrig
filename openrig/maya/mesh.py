"""Mesh utilities."""
import maya.cmds as mc
import maya.api.OpenMaya as om2
from openrig.shared.core import vectors


def getClosestPoint(position, mesh):
    """Return closest vertex on given mesh to the given point.

    :param position: world space coordinate
    :type position: tuple | list

    :param mesh: mesh name
    :type mesh: str

    :returns: point position
    :rtype: tuple
    """
    facePoint = getClosestFacePoint(position, mesh)
    point = facePoint[0].x, facePoint[0].y, facePoint[0].z
    return point


def getMeshFn(mesh):
    """
    :param mesh: mesh name
    :type mesh: str

    :returns: mesh function set
    :rtype: OpenMaya.MFnMesh
    """
    # get MFnMesh
    selList = om2.MSelectionList()
    selList.add(mesh)
    dagPath = selList.getDagPath(0)
    meshFn = om2.MFnMesh(dagPath)

    return meshFn


def getClosestFacePoint(position, mesh):
    """Return closest world point on given mesh to the given point.

    :param position: world space coordinate
    :type position: tuple | list

    :param mesh: mesh name
    :type mesh: str

    :returns: face ID and world point
    :rtype: tuple
    """
    # get MFnMesh
    meshFn = getMeshFn(mesh)

    # get closest face ID
    point = om2.MPoint(position[0], position[1], position[2])
    space = om2.MSpace.kWorld
    closestPoint = meshFn.getClosestPoint(point, space)

    return closestPoint


def getClosestFace(position, mesh):
    """Return closest vertex on given mesh to the given point.

    :param position: world space coordinate
    :type position: tuple | list

    :param mesh: mesh name
    :type mesh: str

    :returns: face name
    :rtype: str
    """
    faceId = getClosestFacePoint(position, mesh)[-1]
    return mesh + '.f[%s]' % faceId


def getClosestVertex(position, mesh):
    """Return closest vertex on given mesh to the given point.

    :param position: world space coordinate
    :type position: tuple | list

    :param mesh: mesh name
    :type mesh: str

    :returns: vertex name
    :rtype: str
    """
    # get closest face ID
    facePoint = getClosestFacePoint(position, mesh)
    faceId = facePoint[-1]

    # get closest vert
    meshFn = getMeshFn(mesh)

    faceVerts = meshFn.getPolygonVertices(faceId)
    closestVertId = None
    distance = None
    for v in faceVerts:
        pos = mc.pointPosition(mesh + '.vtx[%s]' % v)
        pointA = vectors.Point(position[0], position[1], position[2])
        pointB = vectors.Point(pos[0], pos[1], pos[2])
        d = pointA.distance(pointB)
        if distance is None or d < distance:
            distance = d
            closestVertId = v

    return mesh + '.vtx[%s]' % closestVertId


def getClosestUV(position, mesh):
    """Return closest UV on given mesh to the given point.

    :param position: world space coordinate
    :type position: tuple | list

    :param mesh: mesh name
    :type mesh: str

    :returns: UV coordinate
    :rtype: tuple
    """
    # get MFnMesh
    meshFn = getMeshFn(mesh)

    # get closes UV
    point = om2.MPoint(position[0], position[1], position[2])
    uvFace = meshFn.getUVAtPoint(point)
    closestUV = (uvFace[0], uvFace[1])

    return closestUV

