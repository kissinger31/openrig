'''
This will deal with getting, setting, importing, exporting weights.
'''
import maya.cmds as mc
import maya.api.OpenMaya as om2
# using this one for the MItGeometry 
import maya.OpenMaya as OpenMaya

import os
import xml.etree.ElementTree as et
import numpy

from openrig.shared import common
from openrig.maya import weightObject
import openrig.maya.transform as rig_transform
import openrig.maya.blendShape as rig_blendshape
import openrig.maya.skinCluster as rig_skincluster
import openrig.maya.shape as rig_shape

BLENDWEIGHTS_ATTR = 'blendWeights'
SKINCLUSTER_ATTRIBUTE_LIST = ['skinningMethod', BLENDWEIGHTS_ATTR, 'normalizeWeights']

def setWeights(deformer, weights, mapList=None, geometry=None):
    '''
    Sets weights for specified deformers.
    :param deformer: Deformer name
    :type deformer: str
    :param weights: WeightObject or list of numpy arrays or tuples or lists
    :type weights: WeightObject | list | tuple
    :param map: Name of influence or deformer map to assing weights to.
    :type map: str | list
    :return: None
    '''
    # make sure we have the mapList
    if isinstance(mapList, basestring):
        mapList = common.toList(mapList)
    elif mapList == None:
        mapList = getMaps(deformer)

    if geometry:
        if not mc.objExists(geometry):
            raise RuntimeError("{} doesn't exists in the current Maya session!".format(geometry))
        # make sure we have the shape of the geometry for all deformers except the skinCluster
        geoDagPath = rig_transform.getDagPath(geometry)
        geoDagPath.extendToShape()
    else:
        # get the geometry and the iterator to use for looping through the mesh points for wts.
        geometry = mc.deformer(deformer, q=True, g=True)[0]
        geoDagPath = rig_transform.getDagPath(geometry)
        geoDagPath.extendToShape()

    # TODO: If weight array length is longer than the pnt count
    #       it needs to be shortened to match the pnt count.
    pnt_count = rig_shape.getPointCount(geometry) -1

    # make sure we have the correct weights for what we're going to set.
    if isinstance(weights, (list, tuple)):
        weightList = [numpy.array(weights)]
    elif isinstance(weights, numpy.ndarray):
        weightList = [weights]
    elif isinstance(weights, weightObject.WeightObject):
        if not mapList:
            mapList = weights.getMaps()
        weightList = weights.getWeights()

    if mc.nodeType(deformer) == 'skinCluster':
        # iterate through the mesh and set the values on each point
        for mapIndex, inf in enumerate(mapList):
            # find the inf index
            infIndex = None
            con = mc.listConnections(inf+'.worldMatrix[0]', p=True, d=True, s=False)
            for c in con:
                if deformer+'.matrix' in c:
                    infIndex = c.split('[')[1][:-1]
            if infIndex:
                attr = '{}.wl[0:{}].w[{}]'.format(deformer, pnt_count, infIndex)
                # Convert the numpy array to a list so it can be unpacked in setAttr
                weights = weightList[mapIndex].tolist()
                mc.setAttr(attr, *weights)
    elif mc.nodeType(deformer) == 'blendShape':
        for map in mapList:
            #Get indexes
            targetIndex = rig_blendshape.getTargetIndex(deformer, map)
            if targetIndex == -1:
                mc.warning('{}.{} does not exist'.format(deformer, map))
                continue

            map_index = mapList.index(map)
            geometryindex = mc.deformer(deformer,q=True, geometry=True).index(geoDagPath.partialPathName())

            attr = '{}.it[0].itg[{}].tw[0:{}]'.format(deformer, targetIndex, pnt_count)
            # Convert the numpy array to a list so it can be unpacked in setAttr
            weights = weightList[map_index].tolist()
            mc.setAttr(attr, *weights)
    elif 'weightGeometryFilter' in mc.nodeType(deformer, i=True):
        geometryindex = mc.deformer(deformer, q=True, geometry=True).index(geoDagPath.partialPathName())
        attr = '{}.wl[{}].w[0:{}]'.format(deformer, geometryindex, pnt_count)
        # Convert the numpy array to a list so it can be unpacked in setAttr
        weights = weightList[0].tolist()
        mc.setAttr(attr, *weights)

def getWeights(deformer, mapList=None, geometry=None):
    '''
    Gets weights for specified deformers. Geo does not need to be specified unless the deformer has multiple goes.
    :param deformer: Deformer name
    :type deformer: str
    :param map: Name of influence or deformer map to assing weights to.
    :type map: str | list
    :param geometry: Name of geometry to get weights from
    :type geometry: str
    :returns: Returns a weight object that you are able to use or manipulate.
    :rtype: WeightObject
    '''
    weightList = list()
    # make sure there is a mapList
    if not mapList:
        mapList = getMaps(deformer) or list()
    if not isinstance(mapList, (list, tuple)):
        mapList = common.toList(mapList)

    if geometry:
        if not mc.objExists(geometry):
            raise RuntimeError("{} doesn't exists in the current Maya session!".format(geometry))
        # make sure we have the shape of the geometry for all deformers except the skinCluster
        geoDagPath = rig_transform.getDagPath(geometry)
        geoDagPath.extendToShape()
        geometryFullPath = geoDagPath.fullPathName()
    else:
        # get the geometry and the iterator to use for looping through the mesh points for wts.
        geometry = mc.deformer(deformer, q=True, g=True)[0]
        geoDagPath = rig_transform.getDagPath(geometry)
        geoDagPath.extendToShape()
        geometryFullPath = geoDagPath.fullPathName()

    selList = OpenMaya.MSelectionList()
    selList.add(geometryFullPath)
    geoDagPath = OpenMaya.MDagPath()
    selList.getDagPath(0, geoDagPath)
    geoIterator = OpenMaya.MItGeometry(geoDagPath)

    # Get point count
    pnt_count = rig_shape.getPointCount(geometry) -1

    if not mapList:
        weightList = [numpy.array([])]
    else:
        weightList = [numpy.array([]) for map_ in mapList]

    if mc.nodeType(deformer) == 'skinCluster':
        for inf in mapList:
            # get the connections so we can get to the weight list
            infIndex = None
            con = mc.listConnections('{}.worldMatrix[0]'.format(inf), p=True, d=True, s=False)
            for c in con:
                if deformer+'.matrix' in c:
                    infIndex = c.split('[')[1][:-1]
            if infIndex:
                map_index = mapList.index(inf)
                attr = '{}.wl[0:{}].w[{}]'.format(deformer, pnt_count, infIndex)
                values = mc.getAttr(attr)
                # Convert to numpy array and round to 5 decimals
                values = numpy.round(values, 5)
                weightList[map_index] = values

    elif mc.nodeType(deformer) == 'blendShape':
        # iterate over the geometry
        geometryindex = 0

        geoList = mc.ls(mc.deformer(deformer, q=True, geometry=True), l=True)
        if geoList and geometryFullPath in geoList:
            geometryindex = geoList.index(geometryFullPath)

        for map in mapList:
            # Get blendshape target index
            targetIndex = rig_blendshape.getTargetIndex(deformer, map)
            if targetIndex == -1:
                continue
            # Get mapList index
            map_index = mapList.index(map)

            # Define attrs
            attr = '{}.it[0].itg[{}].tw[0:{}]'.format(deformer, targetIndex, pnt_count)
            attr_default_test = '{}.it[0].itg[{}].tw[*]'.format(deformer, targetIndex)

            # When no values have ever been set, the attribute will not exist
            if not mc.objExists(attr_default_test):
                # Generate numpy array of ones for the point count
                values = numpy.ones(pnt_count+1)
            else:
                # Valid values exist, get them
                values = mc.getAttr(attr)
                # Convert to numpy array and round to 5 decimals
                values = numpy.round(values, 5)

            # Add array to weightList
            weightList[map_index] = values

    elif 'weightGeometryFilter' in mc.nodeType(deformer, i=True):
        geoList = mc.ls(mc.deformer(deformer,q=True, geometry=True), l=True)

        if geoList and geometryFullPath in geoList:
            geometryindex = geoList.index(geometryFullPath)

        # Define attrs
        attr = '{}.wl[{}].w[0:{}]'.format(deformer, geometryindex, pnt_count)
        attr_default_test =  '{}.wl[{}].w[*]'.format(deformer, geometryindex)

        # When no values have ever been set, the attribute will not exist
        if not mc.objExists(attr_default_test):
            # Generate numpy array of ones for the point count
            values = numpy.ones(pnt_count+1)
        else:
            # Valid values exist, get them
            values = mc.getAttr(attr)
            # Convert to numpy array and round to 5 decimals
            values = numpy.round(values, 5)

        # Add array to weightList
        weightList[0] = values

    return weightObject.WeightObject(maps=mapList, weights=weightList)

def mirrorWeights(sourceDeformer, sourceGeometry, destinationDeformer=None, destinationGeometry=None, mapList=None, posVector=(-1, 1, 1)):
    '''
    Mirror weights
    This will mirror the weights for the given deformer and maps. If the deformer doesn't have a mirror name then
    we will mirror across the same deformer.
    This will handle going across the center line.
    ..example ::
         mirrorWeights( 'lip_upper_cluster')
    :param deformer: Deformer name
    :type deformer: str
    :param mapList: Name of influence or deformer map to assing weights to.
    :type mapList: str | list
    :param geometry: Name of geometry to get weights from
    :type geometry: str
    :param posVector: Direction you want to mirror the weights.
    :type posVector: str
    '''
    if sourceGeometry:
        if not mc.objExists(sourceGeometry):
            raise RuntimeError("{} doesn't exists in the current Maya session!".format(sourceGeometry))
        # make sure we have the shape of the geometry for all deformers except the skinCluster
        geoDagPath = rig_transform.getDagPath(sourceGeometry)
        geoDagPath.extendToShape()
        geometryFullPath = geoDagPath.fullPathName()
    else:
        # get the geometry and the iterator to use for looping through the mesh points for wts.
        sourceGeometry = mc.deformer(deformer, q=True, g=True)[0]
        geoDagPath = rig_transform.getDagPath(sourceGeometry)
        geoDagPath.extendToShape()
        geometryFullPath = geoDagPath.fullPathName()

    if destinationGeometry:
        if not mc.objExists(destinationGeometry):
            raise RuntimeError("{} doesn't exists in the current Maya session!".format(destinationGeometry))
        # make sure we have the shape of the geometry for all deformers except the skinCluster
        destination_geoDagPath = rig_transform.getDagPath(destinationGeometry)
        destination_geoDagPath.extendToShape()
        destination_geometryFullPath = destination_geoDagPath.fullPathName()
    else:
        destination_geoDagPath = geoDagPath
        destination_geometryFullPath = geometryFullPath

    if mc.objExists('{}Orig'.format(geometryFullPath)):
        selList = om2.MSelectionList()
        selList.add('{}Orig'.format(geometryFullPath))
        geoOrigDagPath = selList.getDagPath(0)
        geoMFnMesh = om2.MFnMesh(geoOrigDagPath)
    else:
        geoMFnMesh = om2.MFnMesh(geoDagPath)

    # create empty point array
    geoPointArray = geoMFnMesh.getPoints(om2.MSpace.kWorld)

    if mc.objExists('{}Orig'.format(destination_geometryFullPath)):
        selList = om2.MSelectionList()
        selList.add('{}Orig'.format(destination_geometryFullPath))
        geoOrigDagPath = selList.getDagPath(0)
        destination_geoMFnMesh = om2.MFnMesh(geoOrigDagPath)
    else:
        destination_geoMFnMesh = om2.MFnMesh(destination_geoDagPath)

    destination_geoPointArray = destination_geoMFnMesh.getPoints(om2.MSpace.kWorld)

    weight_object = getWeights(sourceDeformer, mapList, geometryFullPath)
    # put each point to a list
    weight_list = weight_object.getWeights()
    map_list = weight_object.getMaps()
    point_list = numpy.asarray(geoPointArray[:])
    destination_point_list = numpy.asarray(destination_geoPointArray[:])
    weight_list_array = list()
    # make the posVector an array
    new_pos_vector = numpy.asarray(posVector + tuple([1]))
    # since we don't have a map for envelope, we will set this to be
    if not map_list:
        map_list.append(1)

    for map_index in range(len(map_list)):
        new_weight_list = numpy.zeros(len(geoPointArray))
        value_id_list = numpy.where(weight_list[map_index] > .001)[0]
        value_point_list = numpy.take(point_list, axis=0, indices=value_id_list)
        mirrored_point_list = value_point_list * new_pos_vector

        mirrored_weight_id_list = list()
        for point in mirrored_point_list:
            deltas = destination_point_list - point
            dist_2 = numpy.einsum('ij,ij->i', deltas, deltas)
            mirrored_weight_id_list.append(numpy.argmin(dist_2))

        if not destinationDeformer:
            destinationDeformer = common.getMirrorName(sourceDeformer) or sourceDeformer

        # get mirrored deformer
        numpy.put(new_weight_list, mirrored_weight_id_list, numpy.take(weight_list[map_index], indices=value_id_list))

        # get mirrored deformer
        if destinationDeformer == sourceDeformer:
            from_id_list = numpy.where(numpy.take(numpy.array(destination_point_list), axis=1, indices=0) >= 0.00)[0]

            for i in value_id_list:
                if i in from_id_list:
                    new_weight_list[i] = weight_list[map_index][i]
        weight_list_array.append(new_weight_list)
    new_weight_object = weightObject.WeightObject(maps=mapList, weights=weight_list_array)

    if mc.objExists(destinationDeformer):
        setWeights(destinationDeformer, new_weight_object, geometry=destination_geometryFullPath)

def flipWeights(deformer, mapList=None, geometry=None, posVector=(-1, 1, 1)):
    '''
    Mirror weights
    This will mirror the weights for the given deformer and maps. If the deformer doesn't have a mirror name then
    we will mirror across the same deformer.
    This will handle going across the center line.
    ..example ::
         flipWeights( 'lip_upper_cluster')
    :param deformer: Deformer name
    :type deformer: str
    :param mapList: Name of influence or deformer map to assing weights to.
    :type mapList: str | list
    :param geometry: Name of geometry to get weights from
    :type geometry: str
    :param posVector: Direction you want to mirror the weights.
    :type posVector: str
    '''
    if geometry:
        if not mc.objExists(geometry):
            raise RuntimeError("{} doesn't exists in the current Maya session!".format(geometry))
        # make sure we have the shape of the geometry for all deformers except the skinCluster
        geoDagPath = rig_transform.getDagPath(geometry)
        geoDagPath.extendToShape()
        geometryFullPath = geoDagPath.fullPathName()
    else:
        # get the geometry and the iterator to use for looping through the mesh points for wts.
        geometry = mc.deformer(deformer, q=True, g=True)[0]
        geoDagPath = rig_transform.getDagPath(geometry)
        geoDagPath.extendToShape()
        geometryFullPath = geoDagPath.fullPathName()

    if mc.objExists('{}Orig'.format(geometryFullPath)):
        selList = om2.MSelectionList()
        selList.add('{}Orig'.format(geometryFullPath))
        geoOrigDagPath = selList.getDagPath(0)
        geoMFnMesh = om2.MFnMesh(geoOrigDagPath)
    else:
        geoMFnMesh = om2.MFnMesh(geoDagPath)

    # create empty point array
    geoPointArray = geoMFnMesh.getPoints(om2.MSpace.kWorld)

    weight_object = getWeights(deformer, mapList, geometryFullPath)
    # put each point to a list
    weight_list = weight_object.getWeights()
    map_list = weight_object.getMaps()
    weight_list_array = list()
    point_list = numpy.asarray(geoPointArray[:])
    new_pos_vector = numpy.asarray(posVector + tuple([1]))
    # since we don't have a map for envelope, we will set this to be
    if not map_list:
        map_list.append(1)
    for map_index in range(len(map_list)):
        new_weight_list = numpy.zeros(len(geoPointArray))
        value_id_list = numpy.where(weight_list[map_index] > .001)[0]
        value_point_list = numpy.take(point_list, axis=0, indices=value_id_list)
        mirrored_point_list = value_point_list * new_pos_vector

        mirrored_weight_id_list = list()
        for point in mirrored_point_list:
            deltas = point_list - point
            dist_2 = numpy.einsum('ij,ij->i', deltas, deltas)
            mirrored_weight_id_list.append(numpy.argmin(dist_2))

        # get mirrored deformer
        numpy.put(new_weight_list, mirrored_weight_id_list, numpy.take(weight_list[map_index], indices=value_id_list))

        weight_list_array.append(new_weight_list)

    # create the new weight object and set the weights.
    new_weight_object = weightObject.WeightObject(maps=mapList, weights=weight_list_array)
    setWeights(deformer, new_weight_object, geometry=geometryFullPath)

def isDefault(deformer, map):
    '''
    Querys if any user defined values have been set for the map.
    :param deformer:
    :param map:
    :return: -1    - Does not exist
             True  - Map is default values only
             False - Map has user defined values
    '''

    if not mc.objExists(deformer):
        return -1

    if mc.nodeType(deformer) == 'blendShape':
        targetIndex = rig_blendshape.getTargetIndex(deformer, map)
        if targetIndex == -1:
            return -1
        attr_default_test = '{}.it[0].itg[{}].tw[*]'.format(deformer, targetIndex)

    # When no values have ever been set, the attribute will not exist
    if not mc.objExists(attr_default_test):
        return True
    else:
        return False

def getMaps(deformer):
    '''
    This will return the list of maps that live on the deformer passed into this funciton.
    :param deformer: The deformer name
    :type deformer: str
    :return: List of deformers
    :rtype: list
    '''

    # first we will make sure the deformer exist in the current Maya session
    if not mc.objExists(deformer):
        raise RuntimeError("{} doesn't exist in the current Maya session!".format(deformer))

    if mc.nodeType(deformer) == "skinCluster":
        return mc.skinCluster(deformer, q=True, inf=True)
    elif mc.nodeType(deformer) == "cluster":
        return None

def exportWeights(geometry, deformer, directory):
    '''
    This will export weights for the given deformer into the given directory.
    If the directory doesn't exists. It will create the full path.
    .. example::
        exportWeights("body_geo",
            "body_geo_skinCluster",
            "shows/template/collections/rigrepo/templates/biped/rig/build/base/skin_wts")
        exportWeights(["body_geo",eye_l_geo],
            "cluster1",
            "shows/template/collections/rigrepo/templates/biped/rig/build/base/cluster_wts")
    .. note::
        This is setup to export to only one directory. So typically you will only
        want to export deformers of the same type to the same directory

    :param geometry: The geometry(s) you wish to export the weights for.
    :type geometry: str | list

    :param deformer: This is the deforemr(s) you wish to export
    :type deformer: str | list
    :param directory: The directory you wish to store the deformers passed.
    :type directory: str
    '''
    # importing pubs.ui so we can get the maya main window widget.
    # make sure that we have a list for the rest of the function to work properly
    geoList = common.toList(geometry)
    deformerList = common.toList(deformer)
    files_saved = []

    # check to make sure the directory exists. If it doesn't we will create the directory.
    if not os.path.isdir(directory):
        os.makedirs(directory, 755)
    if not deformerList or not geoList:
        return
    # here we will loop through all of the the deformers and geometry and export the files
    # to the given directory.
    for geo in geoList:
        # adding the geometry to a selection list so I can extend to the shape
        # reliably with out any issues.
        selList = om2.MSelectionList()
        selList.add(geo)
        dagPath = selList.getDagPath(0)
        dagPath.extendToShape()
        # once we have the correct shape. Now we will check it against the other shapes
        geoShape = dagPath.partialPathName()
        for deformer in deformerList:
            # that the given deformer is influencing.
            shapes = mc.deformer(deformer, q=True, g=True)
            # get the difference between the deformer and the deformers influenced by
            if geoShape in shapes:
                skipGeo = list(set(shapes).difference(set([geoShape])))
                # this is where we will export the weights.
                file_name = "{}__{}.xml".format(mc.listRelatives(geoShape, p=True)[0], deformer)
                if mc.nodeType(deformer) == 'skinCluster':

                    mc.deformerWeights(file_name,
                                       skip=skipGeo,
                                       export=True,
                                       deformer=deformer,
                                       path=directory,
                                       at=SKINCLUSTER_ATTRIBUTE_LIST)
                else:
                    mc.deformerWeights(file_name,
                                        skip=skipGeo,
                                        export=True,
                                        deformer=deformer,
                                        path=directory)
                files_saved.append(r'{}/{}'.format(directory, file_name))
    if files_saved:
        return files_saved

def importWeights(geometry, deformer, filepath):
    '''
    This will import weights for the given deformer into the given directory.
    .. example::
        importWeights("body_geo",
            "cluster1",
            "shows/template/collections/rigrepo/templates/biped/rig/build/base/cluster_wts/body_geo__cluster1.xml)
    .. note::
        This is setup to import only one file at a time. We should write something that imports
        multiple files in a directory

    :param geometry: The geometry(s) you wish to import the weights for.
    :type geometry: str

    :param deformer: This is the deforemr(s) you wish to import weights onto
    :type deformer: str
    :param filepath: The filepath you want to use for the weights.
    :type filepath: str
    '''
    if not os.path.isfile(filepath):
        raise RuntimeError("{} is not an existing filepath.".format(filepath))

    # split up the path so we can pass the file name and directory in seperately
    filename = os.path.basename(filepath)
    directory = os.path.dirname(filepath)

    # adding the geometry to a selection list so I can extend to the shape
    # reliably with out any issues.
    selList = om2.MSelectionList()
    is_geo_unique = mc.ls(geometry)
    if not len(is_geo_unique) == 1:
        print('import weights: [ {} ] is not unique'.format(is_geo_unique))
        return
    selList.add(geometry)
    dagPath = selList.getDagPath(0)
    dagPath.extendToShape()
    # once we have the correct shape. Now we will check it against the other shapes
    # that the given deformer is influencing.
    shapes = mc.deformer(deformer, q=True, g=True)
    geoShape = dagPath.partialPathName()

    # get the difference between the deformer and the deformers influenced by
    if geoShape in shapes:
        skipGeo = ";".join(list(set(shapes).difference(set([geoShape]))))

    #import the weights for the given deformer and filepath
    try:
        if mc.nodeType(deformer) == 'skinCluster':
            attribute_list = [attr for attr in SKINCLUSTER_ATTRIBUTE_LIST if attr != BLENDWEIGHTS_ATTR]
            mc.deformerWeights(filename,
                               im=True,
                               deformer=deformer,
                               skip=skipGeo,
                               path=directory,
                               at=attribute_list)
            # if the blend map is in the xml file we will make sure to apply it properly, for
            # some reason maya's import isn't doing it correctly. We will remove once we know it works.
            tree = et.parse(filepath)
            root = tree.getroot()
            # create skinCluster deformer if it doesn't exist in the current session.
            for deformer_tag in root.findall('deformer'):
                for attr in deformer_tag.findall('attribute'):
                    if attr.get('name') == BLENDWEIGHTS_ATTR:
                        value = [float(v) for v in attr.get('value').split(' ')]
                        multi = [int(v) for v in attr.get('multi').split(' ')]
                        for v, i in zip(value, multi):
                            mc.setAttr('{}.{}[{}]'.format(deformer, BLENDWEIGHTS_ATTR, i), v)
        else:
            mc.deformerWeights(filename,
                               im=True,
                               deformer=deformer,
                               skip=skipGeo,
                               path=directory)
        return True
    except:
        print "\ncouldn't apply {} to {}".format(filename, deformer)

def applyWtsDir(directory, includeFilter=None, excludeFilter=None):
    '''
    This function will take a directory with properly named weight files,
    i.e.(geometryName__deformerName.xml), and apply them if both the deformer and geometry
    are in the current scene.
    .. TODO::
        We need to make sure we create the other deformers if they don't exist. Currently We're only
        creating skinClusters.
    If the deformers isn't in the scene but the geometry is, we will create the deformer for you.
    :param directory: Directory path with weight files inside of it.
    :type directory: str
    '''
    directory_list = common.toList(directory)
    # loop through all of the files in the directory and make sure they're weights files.
    skippedFiles = ''
    skipped_file_list = []
    loadedFiles = ''
    loaded_file_list = []
    dir_name = ''

    # Comp files
    files_comped = common.compDirFiles(directory_list)

    # Reverse comped files to ensure top directory files are applied last
    files_comped.reverse()
    directory_list.reverse()

    for i in range(len(directory_list)):
        directory = directory_list[i]
        loadedFiles += '\r\rLoading from: {}'.format(directory)
        loadedFiles += '\r -------------------------------------------------------  \n'
        dir_name = directory.split('/')[-1]

        for filename in files_comped[i]:

            filepath = os.path.join(directory, filename)
            fileSplit = filename.split("__")
            if len(fileSplit) > 2:
                fileSplit[1] = fileSplit[1] + '__' + fileSplit[2]

            # Apply name filters
            if ".xml" != os.path.splitext(filepath)[-1]:
                continue
            if includeFilter != '':
                if includeFilter not in filename:
                    skippedFiles+=('Load filter skipped: ' + filename + '\r')
                    skipped_file_list.append(filename)
                    continue
            if excludeFilter != '':
                if excludeFilter in filename:
                    skippedFiles+=('Load filter skipped: ' + filename + '\r')
                    skipped_file_list.append(filename)
                    continue

            # get the geometry, deformer, and deformerType from the file name.
            geometry = fileSplit[0]
            deformer = fileSplit[1].split(".")[0]
            deformerType = deformer.split("_")[-1]
            # Continue if the geo doesn't exist
            if not mc.objExists(geometry):
                print('Loading {}: Geometry [ {} ] does not exist'.format(deformer, geometry))
                continue
            # if the deformer doesn't exist, then we will create it.
            if not mc.objExists(deformer):
                tree = et.parse(filepath)
                root = tree.getroot()
                # create skinCluster deformer if it doesn't exist in the current session.
                if deformerType == "skinCluster":
                    jointList = [wts.get('source') for wts in root.findall('weights')]
                    jointListExists = mc.ls(jointList)
                    jointListMissing = list(set(jointList) - set(jointListExists))
                    if jointListMissing:
                        print('Loading {}: Missing joints [ {} ]'.format(deformer, jointListMissing))
                    if not jointListExists:
                        print('No joints could be fournd for [ {} ]'.format(deformer))
                        continue
                    skin = mc.skinCluster(jointListExists, geometry, name=deformer, tsb=True)[0]
                    # Set to dual quaternion mode
                    mc.setAttr('{}.skinningMethod'.format(skin), 1)
                if deformerType == "deltaMush":
                    mc.deltaMush(geometry,name=deformer,
                                 smoothingIterations=10,smoothingStep=0.5,
                                 pinBorderVertices=True,envelope=True)
            # apply the weights
            if not mc.objExists(deformer):
                print('deformer does not exist [ {} ]'.format(deformer))
                continue
            # import
            loaded = importWeights(geometry, deformer, filepath)
            if not loaded:
                # Just doing a continue here because the importWeights call prints out it if
                # it did not load.
                continue
            # this ensures that our skinCluster is normalized.
            if deformerType == "skinCluster":
                mc.skinCluster(deformer, e=True, fnw=True)

            loadedFiles += ('Loaded: ' + filename + '\n')
            loaded_file_list.append(filename)

    print(loadedFiles)
    print('[ {} ]: {} loaded, {} skipped'.format(dir_name, len(loaded_file_list), len(skipped_file_list)))

def pruneWeights(deformer, geometry, mapList=None, threshold=.0001):
    '''
    :param deformer: Deformer to be pruned
    :param threshold: Points with weight values be low this will be pruned
    :return: None
    '''
    if mc.nodeType(deformer) in  ['cluster', 'wire']:
        pointCount = mc.polyEvaluate(geometry, v=1)
        attr = deformer + '.wl[0].w[0:{}]'.format(pointCount-1)
        if not mc.objExists(attr):
            return
        values = mc.getAttr(attr)
        nValues = numpy.array(values)
        zeroValues = numpy.where(nValues < threshold)[0]
        if zeroValues.size:
            # Build string array of point indexes to remove
            points = [geometry + '.vtx[{}]'.format(x) for x in zeroValues]

            # Get the deformer set
            deformerSet = mc.listConnections(deformer, type='objectSet')[-1]
            mc.sets(points, remove=deformerSet)

def copyMapsToSkincluster(source_mesh, maps, target_mesh=''):
    '''
    :param source_mesh: Source mesh to query maps from
    :param target_mesh: Target mesh to apply skinCluster data to. If not specified this will just be a duplicate
    of the source mesh named source_mesh+'_maps'
    :param maps:  List of maps or shaders. Multi attribute maps will need the deformer name also (deformer.map)
    :return: str
    '''

    sc = '{}_maps_sc'.format(source_mesh)
    group = '{}_maps_grp'.format(source_mesh)
    bind_group = '{}_bind_grp'.format(source_mesh)
    root_joint = '{}__root__bind'.format(source_mesh)
    maps = common.toList(maps)

    # Validate maps
    map_data = []
    for map in maps:

        # Unpack
        map_data_split = map.split('.')
        node = map_data_split[0]
        attr = None
        if len(map_data_split) > 1:
            attr = map_data_split[1]

        if not mc.objExists(node):
            continue

        weights = getWeights(node, attr, geometry=source_mesh)

        if weights:
            map_data.append([node, attr, weights])

    # Return if no valid map data was found
    if not map_data:
        mc.warning('{}.{} no valid map data found'.format(node, attr))
        return

    # Group
    if not mc.objExists(group):
        mc.createNode('transform', n=group)
        mc.createNode('transform', n=bind_group, parent=group)
        mc.select(cl=1)
        mc.joint(n=root_joint)
        mc.parent(root_joint, bind_group)

    if not mc.objExists(target_mesh):
        # Duplicate
        target_mesh = mc.duplicate(source_mesh, n='{}_maps'.format(source_mesh))[0]
        mc.parent(target_mesh, group)

    # Remove any history on the mesh
    mc.delete(target_mesh, ch=1)

    # Build skinCluster
    # TODO: Remove this selection call
    mc.select(root_joint, target_mesh)
    sc = mc.skinCluster(target_mesh, root_joint, tsb=True, n=sc)[0]
    # Normalization off
    mc.setAttr('{}.normalizeWeights'.format(sc), 1)
    mc.setAttr('{}.envelope'.format(sc), 0)

    # Map joints
    map_joints = []
    for data in map_data:
        node, attr, weights = data
        # Create joint
        mc.select(cl=1)
        joint = mc.joint(n='{}__{}__bind'.format(node, attr))
        mc.parent(joint, bind_group)
        # Add to skincluster
        mc.skinCluster(sc, e=1, addInfluence=joint, lw=True)
        # Set weights
        setWeights(sc, weights, mapList=joint)
        # Lock influence

    # Normalize
    mc.skinPercent(sc, target_mesh, normalize=True)

    return(target_mesh, group)

def copySkinclusterToMaps(source_mesh, target_mesh, maps):
    '''
    :param source_mesh:
    :param target_mesh:
    :param maps:
    :return:
    '''

def copyDeformerWeight(source_mesh, target_mesh, source_deformer, target_deformer, source_map=None, target_map=None):
    if mc.nodeType(source_deformer) in ['blendShape']:
        map = '{}.{}'.format(source_deformer, source_map)
        sc_source_mesh, sc_group = copyMapsToSkincluster(source_mesh, map)
        sc_target_mesh = mc.duplicate(target_mesh, '{}_sc_target_copy'.format(target_mesh))[0]
        sc_target = rig_skincluster.transferSkinCluster(sc_source_mesh,
                                                                 sc_target_mesh,
                                                                 surfaceAssociation="closestPoint")[0]
        inf_name = '{}__{}__bind'.format(source_deformer, source_map)
        weights = getWeights(sc_target, inf_name)
        setWeights(target_deformer, weights, mapList=target_map)
        mc.delete(sc_group, sc_target_mesh)

    if mc.nodeType(source_deformer) in ['cluster']:
        map = source_deformer
        sc_source_mesh, sc_group = copyMapsToSkincluster(source_mesh, map)
        sc_target_mesh = mc.duplicate(target_mesh, '{}_sc_target_copy'.format(target_mesh))[0]
        sc_target = rig_skincluster.transferSkinCluster(sc_source_mesh,
                                                        sc_target_mesh,
                                                        surfaceAssociation="closestPoint")[0]
        inf_name = '{}__{}__bind'.format(source_deformer, source_map)
        weights = getWeights(sc_target, inf_name)
        setWeights(target_deformer, weights, geometry=target_mesh)
        mc.delete(sc_group, sc_target_mesh)

    if mc.nodeType(source_deformer) in ['skinCluster']:
        sc_target = rig_skincluster.transferSkinCluster(source_mesh,
                                                        target_mesh,
                                                        surfaceAssociation="closestPoint")[0]
