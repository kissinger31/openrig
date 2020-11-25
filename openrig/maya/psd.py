"""
This is a module for libraries used for psd.

Glossary
group   - A grouping of interpolator nodes.
interp  - Interpolator node that runs the radial basis functions.
driver  - A node giving input to the interpolator calculation.
pose    - A data point of the interpolator. The interpolator interpolates between the stored
          values of each pose's data point. A pose also has a list of stored values for the
          associated pose controls.
poseControl - Attributes whose values are stored for a giving pose. (Maya=driverController)
              driverControllers and poseControllers
"""

import maya.cmds as mc
import maya.mel as mm
import math

'''     Logging levels
50 CRITICAL
40 ERROR
30 WARNING
20 INFO
10 DEBUG
0  NOTSET
'''
import showtools.maya.deformer as rig_deformer
import showtools.maya.common as rig_common
import showtools.maya.blendShape as rig_blendShape
import logging
import numpy
logger_level = logging.DEBUG
logger = logging.getLogger(__name__)
logger.setLevel(logger_level)
logger_format = '%(levelname)-6s %(funcName)-25s %(message)s  [%(name)s:%(lineno)s]'
loggger_func_len = 0

if not logger.handlers:
    # create console handler
    handler = logging.StreamHandler()
    # create formatter
    formatter = logging.Formatter(logger_format)
    # add formatter to ch
    handler.setFormatter(formatter)
    # add ch to logger
    logger.addHandler(handler)
else:
    handler = logger.handlers[0]
handler.setLevel(logger_level)

# make sure the poseInterpolator plugin is loaded.
mc.loadPlugin("poseInterpolator.so", qt=True)
manager = 'poseInterpolatorManager'

POSE_CONTROL_TYPES ={
                    'bool'         : None,
                    'enum'         : 2,
                    'long'         : 3,
                    'double3'      : 8,
                    'double'       : 6,
                    'doubleLinear' : 6,
                    'doubleAngle'  : 6
                    }

def addInterp(name,
              createNeutralPose=0,
              driver=None,
              regularization=0,
              outputSmoothing=0,
              interpolation=1,
              allowNegativeWeights=1,
              enableRotation=1,
              enableTranslation=0,
              twistAxis=0,
              group=None):
    '''
    :param name: Name of interpolator node
    :param driver: driver name
    :param createNeutralPose: Add swing, twist, and swing/twist neutral pose
    :param twistAxis:
    :return: poseInterpolator
    '''

    parent_length = len(mc.ls('poseInterpolatorManager.poseInterpolatorParent[*]'))
    if driver:
        mc.select(driver)
        interp = mm.eval('createPoseInterpolatorNode("{}", "{}", "{}")'.format(name, createNeutralPose, twistAxis))
    else:
        interp = mc.createNode('poseInterpolator', name='{}Shape'.format(name))
        mc.rename(mc.listRelatives(interp, p=True)[0], name)
        mc.connectAttr('{}.midLayerParent'.format(interp),
                       'poseInterpolatorManager.poseInterpolatorParent[{}]'.format(parent_length), f=True)

    mc.setAttr(interp+'.regularization', regularization)
    mc.setAttr(interp+'.outputSmoothing', outputSmoothing)
    mc.setAttr(interp+'.interpolation', interpolation)
    mc.setAttr(interp+'.allowNegativeWeights', allowNegativeWeights)
    mc.setAttr(interp+'.enableRotation', enableRotation)
    mc.setAttr(interp+'.enableTranslation', enableTranslation)

    # if there is a group passed by the user we will add the group.
    if group:
        addToGroup(interp, group)

    mc.addAttr(interp, ln='blendShape', at='message', multi=True)
    return interp

def getInterp(node):
    '''
    Used to convert a dag node to the interpolator node. If
    a transform is passed a interpoloator shape is returned. If the node is a shape
    and an interpolator, it is just passed through.

    :param node: Any dag node.
    :return: interpoloator node related to the passed node
    '''
    if not node:
        return
    node = rig_common.getFirstIndex(node)
    if not mc.objExists(node):
        return
    if mc.nodeType(node) == 'transform':
        shape = rig_common.getFirstIndex(mc.listRelatives(node, s=1, ni=1))
        if shape:
            node = shape

    if mc.nodeType(node) == 'poseInterpolator':
        return(node)

def getInterpData(node):
    '''
    :param node: Pose interpololator
    :return: dictionary of all the data that makes up the inpterpolator

    Data keys

    interpolator
        regularization
            float
        outputSmoothing
            float
        interpolation
            enum
        allowNegativeWeights
            bool
        trackRotation
            bool
        trackTranslation
            bool
        poses
            type
                enum
            enabled
                bool
            drivenShapes
                numpyArrayIndex
                    numpy file
                        weights
                        deltas
        drivers
            twistAxis
                enum
            eulerTwist
                bool
            controllers
                array

    '''

def addPose(interp, pose, type='swing'):
    '''
    :param interp: Pose interpolator
    :param pose: Pose name
    :param type: options are: swing, twist, and swingandtwist
    :return: Index of added pose
    '''

    index = mm.eval('poseInterpolatorAddPose("{interp}", "{pose}")'.format(interp=interp,
                                                                           pose=pose))
    mm.eval('poseInterpolatorSetPoseType("{interp}", "{pose}", "{type}")'.format(interp=interp,
                                                                                 pose=pose,
                                                                                 type=type))
    pose_name = getPoseName(interp, index)
    setPoseFalloff(interp, pose_name, .3)
    return pose_name

def addToGroup(interp, group_name='Group'):
    '''
    This should add the interpolator to the given group.
    '''
    interp_parent_index = len(mc.ls('poseInterpolatorManager.poseInterpolatorParent[*]'))
    connections = mc.listConnections('{}.midLayerParent'.format(interp), plugs=True)
    if not connections:
        mc.connectAttr('{}.midLayerParent'.format(interp),
                       'poseInterpolatorManager.poseInterpolatorParent[{}]'.format(interp_parent_index), f=True)
    else:
        interp_parent_index = long(connections[0].split('[')[-1].split(']')[0])
    current_group_list = [mc.getAttr('{}.directoryName'.format(parent_attr)) for parent_attr in
                          mc.ls('poseInterpolatorManager.poseInterpolatorDirectory[*]')]

    # check to make sure the group name that was passed is in the current list of groups available.
    if not group_name in current_group_list:
        raise RuntimeError('The group name {} is not in the current list of groups for PSD.'.format(group_name))
    index_list = [parent_attr.split('[')[-1].split(']')[0] for parent_attr in
                  mc.ls('poseInterpolatorManager.poseInterpolatorDirectory[*]')]
    for grp in current_group_list:
        group_index = index_list[current_group_list.index(grp)]
        current_child_indices = mc.getAttr(
            'poseInterpolatorManager.poseInterpolatorDirectory[{}].childIndices'.format(group_index))
        if grp == group_name:
            current_child_indices.append(long(interp_parent_index))
            current_child_indices.sort()
        else:
            if interp_parent_index in current_child_indices:
                current_child_indices.pop(current_child_indices.index(interp_parent_index))

        mc.setAttr('poseInterpolatorManager.poseInterpolatorDirectory[{}].childIndices'.format(group_index),
                   current_child_indices, type='Int32Array')


def getPoseName(interp, index):
    '''
    :param interp: Pose interpolator
    :param index: Index to query pose name from
    :return:
    '''
    interp = getInterp(interp)
    attr = interp+'.pose[{}].poseName'.format(index)
    pose_name = None
    if mc.objExists(attr):
        pose_name = mc.getAttr(interp+'.pose[{}].poseName'.format(index))
    return pose_name

def getPoseWeight(interp, pose):
    '''
    Get the weight output value of the given pose

    :param interp: Pose interpolator
    :param index: Index to weight from
    :return:
    '''
    interp = getInterp(interp)
    index = getPoseIndex(interp, pose)
    attr = interp+'.output[{}]'.format(index)
    if mc.objExists(attr):
        mc.dgdirty(attr)
        value = mc.getAttr(attr)
        return value

def getPoseNames(interp):
    poses = mc.poseInterpolator(interp, q=1, poseNames=1)
    return(poses)

def renamePose(interp, poseName, newName):
    '''

    :param interp: Pose interpolator transform
    :param poseName: Name of pose
    :param newName: New name of pose
    :return: None
    '''
    # api call
    #mm.eval('poseInterpolator -edit -rename {poseName} {newName} {tpl};'.format(tpl=tpl,
    #                                                                            poseName=poseName,
    #                                                                            newName='shoulder_l_down'))
    mm.eval('poseInterpolatorRenamePose {interp} {poseName} {newName}'.format(interp=interp,
                                                                                  poseName=poseName,
                                                                                  newName=newName))

def getPoseIndex(interp, pose):
    index = mm.eval('poseInterpolatorPoseIndex("{}", "{}")'.format(interp, pose))
    if index != -1:
        return(int(index))

def getPoseIndexes(interp):
    poseIndexes = mc.poseInterpolator(interp, q=1, index=1)
    return(poseIndexes)

def getPoseShapeIndex(interp, pose):
    bs = getDeformer(interp)
    if not bs:
        return
    poseIndex = getPoseIndex(interp, pose)
    if not poseIndex:
        return
    connectedTarget = mc.listConnections(interp+'.output[{}]'.format(poseIndex), p=1)
    if connectedTarget:
        targetName = connectedTarget[0].split('.')[1]
        index = getTargetShapeIndex(targetName, bs)
        return(index)

def getTargetShapeIndex(target, bs):
    targetCount = mc.blendShape(bs, q=1, target=1, wc=1)
    i = 0
    n = 0
    while n < targetCount:
        alias = mc.aliasAttr(bs + '.w[{}]'.format(i), q=1)
        if alias == target:
            return i
        if alias:
            n += 1
        i += 1

def getDrivers(interp):
    drivers = mc.poseInterpolator(interp, q=1, drivers=1) or list()
    return(drivers)

def addDriver(interp, driver_list):
    '''
    Add a driver to the interpolator.

    :param interp: Pose interpolator transform
    '''
    interp = getInterp(interp)
    # new drivers to apply
    driver_list = rig_common.toList(driver_list)
    # get the existing driver list
    existing_driver_list = getDrivers(interp) or list()
    driver_attr_index = len(existing_driver_list)

    for driver in driver_list:
        if driver in existing_driver_list:
            continue
        mc.connectAttr('{}.matrix'.format(driver), '{}.driver[{}].driverMatrix'.format(interp, driver_attr_index), f=True)
        if mc.nodeType(driver) == 'joint':
            mc.connectAttr('{}.jointOrient'.format(driver), '{}.driver[{}].driverOrient'.format(interp, driver_attr_index), f=True)
        mc.connectAttr('{}.rotateAxis'.format(driver), '{}.driver[{}].driverRotateAxis'.format(interp, driver_attr_index), f=True)
        mc.connectAttr('{}.rotateOrder'.format(driver), '{}.driver[{}].driverRotateOrder'.format(interp, driver_attr_index), f=True)
        print('Connected {} to {} at driver index {}'.format(driver, interp, driver_attr_index))
        driver_attr_index += 1

def addPoseControl(interp, controlAttr):
    '''
    Maya calls pose controls driver controllers. Each driver has pose controls associated with it.
    Adds anim control as a pose controller (driver controller). When going to a pose this sets up
    what values are set on the driver controllers.

    :param interp: Pose interpolator transform
    :param controlAttr: Anim control and attribute to add to the pose controls for the pose interpolator.
                        Example: shoulder_fk_l.r
    :return: None
    '''
    control_attr_list = rig_common.toList(controlAttr)
    interp = getInterp(interp)
    driver_attr_list = mc.ls(interp + '.driver[0]')
    for controlAttr in control_attr_list:
        for driver_attr in driver_attr_list:
            if not mc.listConnections('{}.driverMatrix'.format(driver_attr)):
                continue
            poseInterpAttr = '{}.driverController'.format(driver_attr)
            current_control_list = []
            interp_attr_list = mc.listAttr(poseInterpAttr, m=True) or list()
            for attr in interp_attr_list:
                pose_control = mc.listConnections('{}.{}'.format(interp, attr), plugs=True)
                if pose_control:
                    current_control_list.append(pose_control[0])
            if controlAttr not in current_control_list:
                index = mm.eval('getNextFreeMultiIndex("{poseInterpAttr}", 1)'.format(poseInterpAttr=poseInterpAttr))
                mm.eval('connectAttr -f "{controlAttr}" "{poseInterpAttr}[{index}]" '.format(controlAttr=controlAttr,
                                                                                     poseInterpAttr=poseInterpAttr,
                                                                                     index=index))

def removePoseControl(interp, controlAttr):
    controlAttr = rig_common.getFirstIndex(controlAttr)
    interp = getInterp(interp)
    poseInterpAttrs = mc.ls(interp + '.driver[0].driverController[*]')
    control = controlAttr.split('.')[0]
    for attr in poseInterpAttrs:
        conControl = rig_common.getFirstIndex(mc.listConnections(attr))
        if control == conControl:
            logger.info('disconnecting:  %s %s ', controlAttr, attr)
            mc.disconnectAttr(controlAttr, attr)

def getPoseControls(interp):
    driversData = mc.ls(interp + '.driver[*]')
    if not driversData:
        return []
    driverData = driversData[0]
    poseControlData = mc.listAttr(driverData + '.driverController', m=1)
    if not poseControlData:
        return(list())
    poseControls = list()
    for control in poseControlData:
        connectedControls = mc.listConnections(interp + '.%s' % control, p=1)
        if connectedControls:
            poseControls += connectedControls
    return(poseControls)

def getPoseControlIndex(interp, poseControl):
    '''
    Get the index of the passed poseControl
    :param interp: pose interpolator
    :param poseControl: Pose control must be the node and the attribute
    :return:
    '''
    # Get all the drivers
    driversData = mc.ls(interp + '.driver[*]')
    driverData = driversData[0]
    poseControlData = mc.listAttr(driverData + '.driverController', m=1)

    for control in poseControlData:
        connectedControls = mc.listConnections(attr, p=1)
        if not connectedControls:
            continue
        #if connectedControls:
        if poseControl == connectedControls[0]:
            # The driver controller array is 1 based for some reason, so subtract 1.
            return int(rig_common.getIndex(control))

def getPoseControlType(interp, pose, poseControl):
    '''
    This is stupid and needs to just test the posecontrol attribute itself, becuase
    the type is not stored in the driver controller data just in the pose controller data...

    :param interp: pose interpolator
    :param poseControl: node.attr - Pose control must be the node and the attribute
    :return:
    '''
    pass
    #attr = getPoseControlBaseAttr(interp, pose, poseControl)
    #attr = attr+'Type'
    #if not mc.objExists(attr):
    #    logger.debug('Attribute does not exist: %s', attr)
    #    return
    #type = mc.getAttr(attr)[0]
    #return(type)

def getPoseControlBaseAttr(interp, pose, poseControl):
    '''
    Builds the attibute for the inter.pose that has the data for the driver controller
    This is very confusing because the poseControl is defined as the driverController on
    interp.driverController, but the data for the type of poseControl it is in the pose attr.
    inter.pose.poseControllerData.poseControllerDataItem.poseControllerDataType.
    ????? Why isn't the type defined in the base driverController attribute.

    :param interp:
    :param pose:
    :param poseControl:
    :return:
    '''
    logger.debug("%s", locals())
    pose_index = getPoseIndex(interp, pose)
    pose_control_index = getPoseControlIndex(interp, poseControl)

    if pose_index != None and pose_control_index !=None:
        # Build pose control value attribute name
        attr = '{}.pose[{}].poseControllerData[0]'.format(interp, pose_index)
        attr += '.poseControllerDataItem[{}]'.format(pose_control_index)
        attr += '.poseControllerDataItem'
        return attr

def getPoseControlRotate(interp, pose, poseControl):
    logger.debug("%s", locals())
    attr = getPoseControlBaseAttr(interp, pose, poseControl)
    attr = attr+'Value'
    if not mc.objExists(attr):
        logger.debug('Attribute does not exist: %s', attr)
        return
    value = mc.getAttr(attr)[0]
    value_in_degrees = [math.degrees(x) for x in value]
    logger.debug('value of attr: %s', value_in_degrees)
    return(value_in_degrees)

def setPoseControlRotate(interp, pose, poseControl, value=[0, 0, 0], radians=False):
    attr = getPoseControlBaseAttr(interp, pose, poseControl)
    attr = attr+'Value'
    if not mc.objExists(attr):
        logger.debug('Attribute does not exist: %s', attr)
        return
    if radians:
        value = [math.radians(x) for x in value]
    mc.setAttr(attr, type='double3', *value)

def getPoseControlData(interp, pose):
    index = getPoseIndex(interp, pose)
    if index == None:
        return
    poseControlData = mc.ls('{}.pose[{}].poseControllerData[0].poseControllerDataItem[*]'.format(interp, index))
    poseControlValues = list()
    for data in poseControlData:
        name = mc.getAttr(data + '.poseControllerDataItemName')
        type = mc.getAttr(data + '.poseControllerDataItemType')
        value = mc.getAttr(data + '.poseControllerDataItemValue')
        if type == 8:
            value = value[0]
        poseControlValues.append([name, type, value])
    return(poseControlValues)

def setPoseControlData(interp, pose, name, value, index=None):
    """
    This will set the attributes for the pose on the interpolator based on what is passed in by the user.

    :param interp: PoseInterpolator name
    :param pose: Pose name
    :param name: Name of the control attribute. e.g. controlName.rotate
    :param type: Control attribute type. e.g rotate = 8
    :param value: Value for attribute. e.g. rotates should be in radians (1.2, 2.0, 3.0]
    :return: None
    """
    # get the pose index.
    pose_index = getPoseIndex(interp, pose)
    # if there is no pose index, we will return
    if pose_index == None:
        return

    # check to make sure that the pose control attribute exist in the scene.
    if not mc.objExists(name):
        raise RuntimeError("The control name you passed isn't an attribute that exist")

    # get the attribute we will use to set the data.
    pose_attr_list = mc.ls('{}.pose[{}].poseControllerData[0].poseControllerDataItem'.format(interp, pose_index))
    for pose_attr in pose_attr_list:
        # get the current name list for each control
        current_name_list = [mc.getAttr('{}.poseControllerDataItemName'.format(attr))for attr in mc.ls('{}[*]'.format(pose_attr))]
        # if the pose control passed is in the current existing pose controls, than we will use that index and update it.
        # otherwise we will use the last index in the poses that is the next available.
        if not current_name_list:
            index = 0
        elif name in current_name_list:
            index = current_name_list.index(name)
        elif index == None:
            index = len(current_name_list)

        poseControlData = '{}[{}]'.format(pose_attr, index)
        # split the name to get the attribute so we can query the type and check it against our constant
        control_attr_split = name.split('.')
        attr_name = control_attr_split[-1]
        node_name = control_attr_split[0]
        attr_type = mc.attributeQuery(attr_name, node=node_name, at=True)
        # if the attribute is in our constant, than we will allow you to do the deed.
        if not POSE_CONTROL_TYPES.has_key(attr_type):
            raise RuntimeError('{} is not a valid type for PSD interpolator'.format(attr_type))

        # set the poses data
        mc.setAttr(poseControlData + '.poseControllerDataItemName', name, type='string')
        type = POSE_CONTROL_TYPES[attr_type]
        mc.setAttr(poseControlData + '.poseControllerDataItemType', type)
        if type == 8:
            mc.setAttr(poseControlData + '.poseControllerDataItemValue', *value, type='double3')
        else:
            mc.setAttr(poseControlData + '.poseControllerDataItemValue', value)

def getDeformer(interp):
    # Mel call
    # poseInterpolatorConnectedShapeDeformers

    interp = getInterp(interp)
    poses = getPoseNames(interp) or []
    neutral_poses = [pose for pose in poses if 'neutral' in pose]
    if len(poses) == len(neutral_poses):
        if mc.objExists('{}.blendShape'.format(interp)):
            con = mc.listConnections('{}.blendShape'.format(interp))
            if con:
                if mc.nodeType(con[0]) == 'blendShape':
                    return(con[0])
        return None
    indexes = getPoseIndexes(interp)
    for pose, index in zip(poses, indexes):
        con = mc.listConnections(interp+'.output[{index}]'.format(index=index))
        if con:
            if mc.nodeType(con[0]) == 'blendShape':
                return(con[0])

def goToPose(interp, pose, symmetry=True):
    mm.eval('poseInterpolatorGoToPose "{}" "{}"'.format(interp, pose))
    if symmetry:
        mirror_interp = getMirrorInterp(interp)
        mirror_pose = getMirrorPose(interp, pose)
        if mirror_interp and mirror_pose:
            mm.eval('poseInterpolatorGoToPose "{}" "{}"'.format(mirror_interp, mirror_pose))

def goToNeutralPose(interp):
    interp_list = rig_common.toList(interp)
    for interp in interp_list:
        poses = getPoseNames(interp) or list()
        if not poses:
            continue
        for pose in poses:
            if pose == 'neutral':
                goToPose(interp, pose, symmetry=False)

def updatePose(interp, pose):
    '''
    :param interp: Pose interpolator transform
    :param pose: Name of pose
    :return: None
    '''
    # not sure we need this call anymore. We're now handling setting of data on our end.
    mm.eval('poseInterpolator -edit -updatePose {pose} {interp}'.format(interp=interp, pose=pose))
    # this is where we loop through and make sure we're setting the pose data properly.
    control_attr_list = getPoseControls(interp)
    for control_attr in control_attr_list:
        # get the value
        attr_value = mc.getAttr(control_attr)
        # split the name so we can query the type of attribute, incase it's a double3
        control_attr_split = control_attr.split('.')
        attr_name = control_attr_split[-1]
        node_name = control_attr_split[0]
        attr_type = mc.attributeQuery(attr_name, node=node_name, at=True)
        print attr_type, attr_value
        if attr_type == 'double3':
            attr_value = attr_value[0]
            attr_value = [mm.eval('deg_to_rad({})'.format(value)) for value in attr_value]
        elif attr_type in ['doubleAngle']:
            attr_value = mm.eval('deg_to_rad({})'.format(attr_value))
        setPoseControlData(interp, pose, control_attr, attr_value)

def syncPose(interp, pose):
    goToPose(interp, pose)
    updatePose(interp, pose)

def setPoseKernalFalloff(interp, pose):
    '''
    Auto adjusts the gaussian falloff for a more normalized overlap between poses
    :param interp: Pose interpolator
    :param pose: Pose name
    :return: None
    '''
    mm.eval('poseInterpolatorCalcKernelFalloff"{}" "{}"'.format(interp, pose))

def setPoseFalloff(interp, pose, value):
    '''
    Sets the kernnal falloff of the pose. These values are 0-1, and only apply when the interp is in
    gaussian interpolation mode.

    :param interp: interp
    :param pose:  pose
    :param value:  Float to set the pose falloff to

    '''
    index = getPoseIndex(interp, pose)
    if value > 1.0:
        value = 1.0
    if value < 0.0:
        value = 0.0
    mc.setAttr('{}.pose[{}].poseFalloff'.format(interp, index), value)

def getPoseFalloff(interp, pose):
    '''
    Gets the kernnal falloff of the pose. These values are 0-1, and only apply when the interp is in
    gaussian interpolation mode.

    :param interp: interp
    :param pose:  pose
    :return:
    '''
    index = getPoseIndex(interp, pose)
    value = mc.getAttr('{}.pose[{}].poseFalloff'.format(interp, index))
    return(value)

def addShape(interp, pose, bs=None):
    interp = getInterp(interp)

    if not bs:
        bs = getDeformer(interp)
    if not bs:
        return

    shapeIndex = mm.eval('doBlendShapeAddTarget("{bs}", 1, 1, "", 0, 0, {{}})'.format(bs=bs))[0]
    mc.aliasAttr(pose, bs+'.w[{index}]'.format(index=shapeIndex))

    poseIndex = getPoseIndex(interp, pose)
    mc.connectAttr(interp+'.output[{}]'.format(poseIndex), bs+'.w[{}]'.format(shapeIndex))

def remShape(interp, pose, bs=None):
    interp = getInterp(interp)

    if not bs:
        bs = getDeformer(interp)
    if not bs:
        return

    shapeIndex = mm.eval('doBlendShapeAddTarget("{bs}", 1, 1, "", 0, 0, {{}})'.format(bs=bs))[0]
    mc.aliasAttr(pose, bs+'.w[{index}]'.format(index=shapeIndex))

    poseIndex = getPoseIndex(interp, pose)
    mc.connectAttr(interp+'.output[{}]'.format(poseIndex), bs+'.w[{}]'.format(shapeIndex))

def getAllGroups():
    groupIndexes = mc.ls(manager + '.poseInterpolatorDirectory[*]')
    groups = list()
    for group in groupIndexes:
        name = mc.getAttr(group + '.directoryName')
        # Ignore the default groups named "Group"
        if name == 'Group':
            continue
        # Ignore groups with no interpolator children
        if not getGroupChildren(name):
            continue
        groups.append(name)
    return groups

def getGroupChildren(group):
    # Directories are any pose interpoloator group
    groupAttrs = mc.ls(manager + '.poseInterpolatorDirectory[*]')
    for groupAttr in groupAttrs:
        name = mc.getAttr(groupAttr + '.directoryName')
        if name != group:
            continue

        childAttrs = mc.getAttr(groupAttr + '.childIndices')
        if not childAttrs:
            return []
        children = list()
        for childAttr in childAttrs:
            childAttr = int(childAttr)
            # The child index is -2 if there are no children
            # or if the only child is a group, guessing...
            if childAttr == -2:
                continue
            child = mc.listConnections(manager+'.poseInterpolatorParent[{}]'.format(childAttr))
            child = rig_common.getFirstIndex(child)
            child = getInterp(child)
            if child:
                children.append(child)
        return(children)

def getGroup(interp):
    interp = getInterp(interp)
    if not interp:
        return
    con = mc.listConnections(interp+'.midLayerParent', p=1)
    con = rig_common.getFirstIndex(con)
    index = int(con.split('[')[1].replace(']',''))
    groups = mc.ls(manager + '.poseInterpolatorDirectory[*]')
    for group in groups:
        name = mc.getAttr(group + '.directoryName')
        childIndices = mc.getAttr(group + '.childIndices')
        if index in childIndices:
            return(name)

def deleteGroup(group):
    '''
    Delete all interpoloators and targets for the given group
    :param group:
    :return: None
    '''
    if not group in getAllGroups():
        mc.warning('psd group [ {} ] does not exist'.format(group))
        return
    interps = getGroupChildren(group)
    if interps:
        deleteInterp(interps)

def deleteInterp(interp):
    '''
    Delete interpolaotr and it's poses and drivens.
    :param interp:
    :return:
    '''
    pass

def deletePose(interp, pose):
    '''
    Delete the pose and its drivens
    :param interp:
    :param pose:
    :return:
    '''
    pose_list = rig_common.toList(pose)
    for pose in pose_list:
        mm.eval('poseInterpolatorDeletePose("{}", "{}")'.format(interp, pose))

def deleteDriven(interp, pose, driven):
    '''
    Delete the driven for the given pose
    :param interp:
    :param pose:
    :return:
    '''
    pass

def disablePose(interp, pose):
    interp = getInterp(interp)
    poseIndex = getPoseIndex(interp, pose)
    mc.setAttr('{}.pose[{}].isEnabled'.format(interp, poseIndex), 0)

def enablePose(interp, pose):
    interp = getInterp(interp)
    poseIndex = getPoseIndex(interp, pose)
    mc.setAttr('{}.pose[{}].isEnabled'.format(interp, poseIndex), 1)

def disableInterp(interp):
    setInterpEnableState(interp, False)

def enableInterp(interp):
    setInterpEnableState(interp, True)

def setInterpEnableState(interp, state):
    interp = getInterp(interp)
    if not interp:
        return

    orig_state = isEnabled(interp)
    if not mc.objExists('{}.enabled'.format(interp)):
        mc.addAttr(interp, ln='enabled', at='bool')
    if not mc.objExists('{}.enabledPoses'.format(interp)):
        mc.addAttr(interp, ln='enabledPoses', dt='string')

    all_pose_list = getPoseNames(interp) or []
    active_enabled_pose_list = getEnabledPoses(interp)

    # Get stored enabled poses
    stored_enabled_pose_list = mc.getAttr(interp+'.enabledPoses')
    if stored_enabled_pose_list:
        stored_enabled_pose_list = eval(stored_enabled_pose_list)
    else:
        stored_enabled_pose_list = all_pose_list

    # Enable
    if state:
        pose_list = stored_enabled_pose_list
        # If no poses are enabled then just turn them all on
        if not active_enabled_pose_list and not stored_enabled_pose_list:
            pose_list = all_pose_list
        for pose in pose_list:
            if isValid(interp, pose):
                enablePose(interp, pose)
    # Disable
    else:
        for pose in active_enabled_pose_list:
            disablePose(interp, pose)
        # Store enabled poses
        mc.setAttr(interp+'.enabledPoses', active_enabled_pose_list, type='string')

    mc.setAttr('{}.enabled'.format(interp), state)

    return orig_state

def getEnabledPoses(interp):
    interp = getInterp(interp)
    pose_name_list = getPoseNames(interp) or []
    enabled_poses = []
    for pose in pose_name_list:
        if isEnabled(interp, pose):
            enabled_poses.append(pose)
    return enabled_poses

def setPoseEnableState(interp_pose_list, state=True):
    '''
    :param interp_pose_list: List of tuples [(interp, pose)]. Each tuple should be an interp and a pose on
    that interp you want disabled before matching the geo.
    This is generally for poses that have blendmaps controlling the overlap between multiple poses.
    For the maps blending to work correctly the poses that "overlap" the pose you are applying
    need to be disable so that the same deltas will be on all the overlapping poses.
    '''

    # Edit pose states and track poses changed in the posses changed list
    poses_changed_list = []
    for interp_pose_item in interp_pose_list:
        interp, pose = interp_pose_item
        # disable
        if state:
            if isEnabled(interp, pose):
                disablePose(interp, pose)
                poses_changed_list.append(interp_pose_item)
        # enable
        else:
            if not isEnabled(interp, pose):
                enablePose(interp, pose)
                poses_changed_list.append(interp_pose_item)

    return(poses_changed_list)


def isEnabled(interp, pose=None):
    interp = getInterp(interp)
    if pose:
        poseIndex = getPoseIndex(interp, pose)
        state = mc.getAttr('{}.pose[{}].isEnabled'.format(interp, poseIndex))
        return(state)
    else:
        all_pose_list = getPoseNames(interp) or []
        for pose in all_pose_list:
            if isEnabled(interp, pose):
                return(True)
        if not all_pose_list:
            if mc.objExists('{}.enabled'.format(interp)):
                return mc.getAttr('{}.enabled'.format(interp))
        return False

def isValid(interp, pose=None):
    # Pose
    if pose:
        if not getInterp(interp):
            return False
        if getPoseIndex(interp, pose) != None:
            return True
    # Interp only
    else:
        if getInterp(interp):
            return True
    return False

def duplicatePoseShape(interp, pose):

    # Verify there is a shape to duplicate
    bs = getDeformer(interp)
    if not bs:
        return

    # Get the connected geo
    geo = mc.deformer(bs, q=1, g=1)
    if not geo:
        return
    # Only deal with one driven geo for now
    geo = geo[0]

    # Get the psd group
    group = getGroup(interp)
    if not group:
        return

    group_grp = '{}_grp'.format(group)
    if not mc.objExists(group_grp):
        mc.createNode('transform', n=group_grp)

    interp_nice_name = getInterpNiceName(interp)
    interp_grp = '{}_interp'.format(interp_nice_name)
    if not mc.objExists(interp_grp):
        mc.createNode('transform', n=interp_grp, p=group_grp)

    # Go to pose
    goToPose(interp, pose)

    # Duplicate geo
    geo_dup = mc.duplicate(geo, n=pose)[0]
    mc.parent(geo_dup, interp_grp)

    # Set tag
    setPoseShapeTag(geo_dup, bs, interp, pose)

    return(geo_dup)

def getMirrorPose(interp, pose):
    mirror_interp = rig_common.getMirrorName(interp)
    mirror_pose = rig_common.getMirrorName(pose) or pose
    if isValid(mirror_interp, mirror_pose):
        return(mirror_pose)

def getMirrorInterp(interp):
    mirror_interp = rig_common.getMirrorName(interp)
    return getInterp(mirror_interp)

def applyPose(interp, pose, bs, geo):
    '''

    :param interp: Interpolator
    :param pose: pose
    :param bs: blendshape
    :param geo: Target geo the pose should match
    :return: None
    '''
    # Got to pose
    goToPose(interp, pose)
    # Invert
    values = geo_trs_zero(geo, bs)
    rig_blendShape.invertShape(bs, pose, geo)
    geo_trs_restore(geo, values)

def applyPoseSymmetry(interp, pose, bs, geo):
    mirror_interp = getMirrorInterp(interp)
    mirror_pose = getMirrorPose(interp, pose)

    if mirror_interp and mirror_pose:
        # Side A
        mirror_state = isEnabled(mirror_interp)
        disableInterp(mirror_interp)
        print('Applying symmetric [ {} ] [ {} ]'.format(pose, interp))
        applyPose(interp, pose, bs, geo)

        # Side B
        enableInterp(mirror_interp)
        state = isEnabled(interp)
        disableInterp(interp)
        print('Applying symmetric [ {} ] [ {} ]'.format(mirror_pose, mirror_interp))
        applyPose(mirror_interp, mirror_pose, bs, geo)

        # Restore states
        setInterpEnableState(mirror_interp, mirror_state)
        setInterpEnableState(interp, state)
    else:
        print('Applying [ {} ] [ {} ]'.format(pose, interp))
        applyPose(interp, pose, bs, geo)


def geo_trs_zero(geo, bs):
    '''
    Note: This should probably be reference the deformed geo's matrix
    :param geo: Geo transform to zero out transformations
    :return: trs values
    '''
    deformed_geo = mc.deformer(bs, q=1, g=1)
    if deformed_geo:
        deformed_geo = mc.listRelatives(deformed_geo, p=1)[0]

    if mc.nodeType(geo) != 'transform':
        geo = mc.listRelatives(geo, s=1, ni=1)[0]

    attrs = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'v']
    values = []
    for a in attrs:
        attr = geo+'.'+a
        mc.setAttr(attr, l=0)
        value = mc.getAttr(attr)
        values.append(value)

    try:
        mc.delete(mc.parentConstraint(deformed_geo, geo))
    except:
        pass

    return values

def geo_trs_restore(geo, values):
    '''
    :param geo: geo transform to restore values to
    :param values: Values to restore
    :return: None
    '''
    attrs = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'v']
    for i in range(len(attrs)):
        attr = geo+'.'+attrs[i]
        try:
            mc.setAttr(attr, values[i])
        except:
            pass

def setPoseShapeTag(shape_transform, bs, interp, pose):
    '''
    Tag duplicated shapes so what pose they came from can be queried
    '''
    if not mc.objExists(shape_transform + '.mix_blendshape'):
        mc.addAttr(shape_transform, dt='string', ln='mix_blendshape')
    mc.setAttr(shape_transform + '.mix_blendshape', bs, type='string')

    if not mc.objExists(shape_transform + '.mix_interpolator'):
        mc.addAttr(shape_transform, dt='string', ln='mix_interpolator')
    mc.setAttr(shape_transform + '.mix_interpolator', interp, type='string')

    if not mc.objExists(shape_transform + '.mix_pose'):
        mc.addAttr(shape_transform, dt='string', ln='mix_pose')
    mc.setAttr(shape_transform + '.mix_pose', pose, type='string')

def getPoseShapeTag(shape_transform):
    bs = None
    interp = None
    pose = None

    if mc.objExists(shape_transform + '.mix_blendshape'):
        bs = mc.getAttr(shape_transform + '.mix_blendshape')
    else:
        return (None)

    if mc.objExists(shape_transform + '.mix_interpolator'):
        interp = mc.getAttr(shape_transform + '.mix_interpolator')
    else:
        return (None)

    if mc.objExists(shape_transform + '.mix_pose'):
        pose = mc.getAttr(shape_transform + '.mix_pose')
    else:
        return (None)

    return (bs, interp, pose)

def getPoseShapes(interp, pose):
    interp_nul = getInterpNiceName(interp) + '_interp'
    pose_shape = interp_nul + '|' + pose
    if mc.objExists(pose_shape):
        return(pose_shape)

def poseLiveToggle(interp, pose):
    '''
    Activates pose for live editing
    '''
    bs = getDeformer(interp)
    if not bs:
        return
    geo = mc.deformer(bs, q=1, g=1)
    if not geo:
        return
    geo = geo[0]
    index = getPoseShapeIndex(interp, pose)
    state = False
    if index != None:
        # Activate
        current_index = mc.getAttr('{}.inputTarget[0].sculptTargetIndex'.format(bs))
        mc.sculptTarget(bs, e=1, target=-1)
        if index != current_index:
            connections = hideWires(geo)
            mc.sculptTarget(bs, e=1, target=index)
            showWires(connections)
            state = True

        # HUD display
        mm.eval('updateBlendShapeEditHUD;')
    return(state)


def hideWires(geo):
    # Make sure we have the shape
    geo = rig_deformer.getShape(geo)

    hist = [geo] + mc.listHistory(geo, pdo=1, il=2)
    connections_to_restore = []
    connections_to_make = []

    # Travers back through the history and severe the wires from it
    # and store the severed connections

    cut = False
    cut_end_attr = None

    for i in range(len(hist)):

        # Make sure we are not at the end of of the history nodes
        if i == len(hist)-1:
            continue

        current = hist[i]
        next = hist[i+1]

        # Find the correct input geo attribute of the node
        if mc.nodeType(current) == 'mesh':
            current_attr = '{}.inMesh'.format(current)
        else:
            current_attr = rig_deformer.getGeoInputAttr(current, geo)

        # Find the connected attribute to the current nodes input
        current_attr_input = mc.listConnections(current_attr, p=1)[0]

        # START CUT
        #
        # Next deformer is a wire current deformer is not
        if mc.nodeType(next) == 'wire' and mc.nodeType(current) != 'wire':

            # start the cut - we have a wire connected to another node, find its connection
            #                 store it and then cut it.
            if not cut:
                connections_to_restore.append([current_attr_input, current_attr])
                cut_end_attr = current_attr

            # Let the loop know the cut has begun
            cut = True

        # END CUT
        #
        # Next is not a wire current is
        if mc.nodeType(next) != 'wire' and mc.nodeType(current) == 'wire':
            # stop the cut
            if cut:
                connections_to_restore.append([current_attr_input, current_attr])
                connections_to_make.append([current_attr_input, cut_end_attr])
            cut = False

    # Make the connections that skip the wires
    for connection in connections_to_make:
        mc.connectAttr(connection[0], connection[1], f=1)

    # Return the connections that need to be restored to get back to the original state
    return connections_to_restore

def showWires(connections):
    for c in connections:
        if not mc.isConnected(c[0], c[1]):
            mc.connectAttr(c[0], c[1], f=1)

def isPoseLive(interp, pose):
    bs = getDeformer(interp)
    pose_index = getPoseShapeIndex(interp, pose)
    live_index = mc.getAttr(bs+'.inputTarget[0].sculptTargetIndex')

    if pose_index == live_index:
        return True

def getLivePoses():
    bs_live_attr_list = mc.ls('*.inputTarget[0].sculptTargetIndex')
    bs_live_list = []
    for bs_attr in bs_live_attr_list:
        index = mc.getAttr(bs_attr)
        bs = bs_attr.split('.')[0]
        if index != -1:
            target_name = mc.aliasAttr(bs + '.w[{}]'.format(index), q=1)
            bs_live_list.append((bs, target_name))

    return (bs_live_list)

def getInterpNiceName(interp):
    interp = getInterp(interp)
    interp_name = interp.replace('_poseInterpolatorShape', '')
    interp_name = interp_name.replace('_driver', '')
    return(interp_name)

def getPoseNiceName(pose):
    pass

def mirrorDelta(interp, pose):
    # Get Deltas
    bs = getDeformer(interp)
    index = getPoseShapeIndex(interp, pose)
    mirror_pose = rig_common.getMirrorName(pose) or pose
    mirror_interp = rig_common.getMirrorName(interp) or interp
    mirror_index = getPoseShapeIndex(mirror_interp, mirror_pose)

    deltas, indices = rig_blendShape.getTargetDeltas(bs, index)
    if not deltas:
        return

    # Center interp mirror
    if interp == mirror_interp and pose == mirror_pose:
        rig_blendShape.setTargetDeltas(bs, deltas, indices, mirror_index)
        mc.blendShape(bs, e=True, mt=(0, mirror_index), ss=1, sa='x')
        print('Center mirror deltas: [ {} ] [ {} ]'.format(interp, pose))

    # Center interp flip
    if interp == mirror_interp and pose != mirror_pose:
        rig_blendShape.setTargetDeltas(bs, deltas, indices, mirror_index)
        mc.blendShape(bs, e=True, ft=(0, mirror_index), ss=1, sa='x')
        print('Flipped deltas: [ {} ] [ {} ]'.format(interp, mirror_pose))

    # Left to right interp mirror
    if interp != mirror_interp and pose != mirror_pose:
        rig_blendShape.clearTargetDeltas(bs, mirror_index)
        rig_blendShape.setTargetDeltas(bs, deltas, indices, mirror_index)
        values = rig_blendShape.getTargetMapWeights(bs, mirror_pose)
        mc.blendShape(bs, e=True, ft=(0, mirror_index), ss=1, sa='x')
        rig_blendShape.setTargetMapWeights(bs, mirror_pose, values)
        print('Left/Right mirrored deltas: [ {} ] [ {} ]'.format(mirror_interp, mirror_pose))
