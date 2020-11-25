import openrig.maya.data.maya_data as maya_data
import openrig.shared.common as common
import openrig.maya.psd as rig_psd
from collections import OrderedDict
import maya.cmds as mc
import traceback


class PSDData(maya_data.MayaData):
    def __init__(self):
        super(PSDData, self).__init__()

    def gatherData(self, node):
        """
        Get all data related to the interpolater (node) and it's poses
        """
        super(PSDData, self).gatherData(node)

        data = OrderedDict()

        # Interpolator settings
        data['regularization'] = mc.getAttr('{}.regularization'.format(node))
        data['outputSmoothing'] = mc.getAttr('{}.outputSmoothing'.format(node))
        data['interpolation'] = mc.getAttr('{}.interpolation'.format(node))
        data['allowNegativeWeights'] = mc.getAttr('{}.allowNegativeWeights'.format(node))
        data['enableRotation'] = mc.getAttr('{}.enableRotation'.format(node))
        data['enableTranslation'] = mc.getAttr('{}.enableTranslation'.format(node))

        # Drivers
        data['drivers'] = OrderedDict()
        driver_indexes = []

        for driver in mc.ls('%s.driver[*]' % node):

            # If no driver is connected continue on
            if not mc.listConnections(driver+'.driverMatrix'):
                continue

            data['drivers'][driver] = OrderedDict()

            # Controllers will be a list under the driver key
            data['drivers'][driver]['controllers'] = []

            # NOTE: Driver controllers are pose controls. These are the controls
            #       with stored values to put the rig into the pose the shape was made for.

            # Is a driver controller connected, could be any number of them
            controllers = mc.listAttr(driver + '.driverController', m=1)

            # Add connected driver controllers
            if controllers:
                for ctrl in controllers:
                    plug = mc.listConnections(node + '.%s' % ctrl, p=1)
                    if not plug:
                        continue
                    plug = plug[0]
                    driver_index = common.getIndex(ctrl)
                    driver_indexes.append(driver_index)
                    plug = str(plug)
                    data['drivers'][driver]['controllers'].append(plug)

            # twistAxis
            value = mc.getAttr(driver+'.driverTwistAxis')
            data['drivers'][driver]['driverTwistAxis'] = value
            # eulerTwist
            value = mc.getAttr(driver+'.driverEulerTwist')
            data['drivers'][driver]['driverEulerTwist'] = value

        # Poses is a order dict that will hold all individual pose data
        data['poses'] = OrderedDict()

        # Get poses - This could have potential index gaps if poses have been deleted
        #             So this attr and index will be used to query but a gapless index
        #             order will be written to the file.
        #
        #             WARNING: Not sure if this new index order will match
        #                      up with the other interp data
        #
        poses = mc.ls('%s.pose[*]' % node)

        i = 0
        for pose in poses:

            # Pose export is the pose attribute at the index that will avoid gaps
            pose_export = '{}.pose[{}]'.format(node, i)

            # pose_export attribute will be a ordered dict under the poses key
            data['poses'][pose_export] = OrderedDict()

            # Controllers
            data['poses'][pose_export]['controllers'] = OrderedDict()

            # Driver indexes are populated in the previous drivers loop
            for driver_index in driver_indexes:

                # Note: interp.pose and interp.driver are multi attrs, where
                #       interp.pose references back to the interp.driver by
                #       index for the sub attr interp.pose.poseControllerData[driver_index] mulit attr.
                #       This organization is insane and confusing as HECK.
                #       So each index in interp.pose.poseControllerData.poseControllerDataItem refers to a
                #       anim control (pose control, driver controller!) for going to the pose.
                #       Why this is under poseControllerData which is indexed by the driver I have no idea.
                #
                data_attr = pose + '.poseControllerData[{}]'.format(driver_index) + '.poseControllerDataItem[*]'
                dataItems = mc.ls(data_attr)

                for di in dataItems:

                    # Replace the pose attr with the pose_export attr to ensure there are no index gaps
                    # that may have happened if poses where deleted in the scene and new ones added.
                    #
                    di_export = di.replace(pose, pose_export)

                    diDict = OrderedDict()
                    diDict['name'] = mc.getAttr(di + '.poseControllerDataItemName')
                    diDict['type'] = mc.getAttr(di + '.poseControllerDataItemType')
                    diDict['value'] = mc.getAttr(di + '.poseControllerDataItemValue')
                    data['poses'][pose_export]['controllers'][di_export] = diDict

            # Settings
            attrs = [
                'poseName',
                'isEnabled',
                'poseType',
                'isIndependent',
                'poseFalloff',
                'poseRotationFalloff',
                'poseTranslationFalloff',
                ]
            for attr in attrs:
                value = mc.getAttr(pose+'.'+attr)
                data['poses'][pose_export][attr] = value

            # Drivens
            poseIndex = common.getIndex(pose)
            attr = '{}.output[{}]'.format(node, poseIndex)
            if mc.objExists(attr):
                drivens = mc.listConnections(attr, p=1)
                data['poses'][pose_export]['drivens'] = drivens

            i += 1

        self._data[node].update(data)

    def applyData(self, nodes, mirror=False):
        """
        """
        for poseInterp in nodes:
            if not poseInterp in self._data:
                print('psd load: missing poseInterp', poseInterp)
                continue
            # Driver controller - per interp
            #
            for drvr in self._data[poseInterp]['drivers'].keys():
                ctrlrs = self._data[poseInterp]['drivers'][drvr]['controllers']
                for ctrl in ctrlrs:
                    index = ctrlrs.index(ctrl)
                    try:
                        mc.connectAttr(ctrl, drvr + '.driverController[%s]' % index, f=1)
                    except:
                        pass

            # Pose controllers - per pose
            #
            i = 0
            for pose in self._data[poseInterp]['poses'].keys():
                dataItems = self._data[poseInterp]['poses'][pose]['controllers'].keys()
                i += 1
                for item in dataItems:
                    name = self._data[poseInterp]['poses'][pose]['controllers'][item]['name']
                    ptype = self._data[poseInterp]['poses'][pose]['controllers'][item]['type']
                    value = self._data[poseInterp]['poses'][pose]['controllers'][item]['value']

                    if isinstance(value, list):
                        value = value[0]
                    try:
                        mc.setAttr(item + '.poseControllerDataItemName', name, type='string')
                        mc.setAttr(item + '.poseControllerDataItemType', ptype)
                        if isinstance(value, tuple) or isinstance(value, list):
                            mc.setAttr(item + '.poseControllerDataItemValue', *value, type='float3')
                        else:
                            mc.setAttr(item + '.poseControllerDataItemValue', value)
                    except:
                        traceback.print_exc()

class PSDDataNew(maya_data.MayaData):
    def __init__(self):
        super(PSDDataNew, self).__init__()

    def gatherData(self, node):
        """
        Get all data related to the interpolater (node) and it's poses
        """
        super(PSDDataNew, self).gatherData(node)

        data = OrderedDict()

        # Interpolator settings
        data['group'] = rig_psd.getGroup(node)
        if not mc.objExists('{}.enabled'.format(node)):
            mc.addAttr(node, ln='enabled', at='bool', dv=True)
        data['isEnabled'] = mc.getAttr('{}.enabled'.format(node))
        attr_list = ['regularization', 'outputSmoothing', 'interpolation',
                     'allowNegativeWeights', 'enableRotation', 'enableTranslation']
        # loop through the attr list and store the value
        for attr in attr_list:
            data[attr] = mc.getAttr('{}.{}'.format(node, attr))

        # Drivers
        data['drivers'] = OrderedDict()
        driver_indexes = []

        for driver in mc.ls('%s.driver[*]' % node):
            driver_connection = mc.listConnections(driver + '.driverMatrix')
            # If no driver is connected continue on
            if not driver_connection:
                continue

            data['drivers'][driver] = OrderedDict()
            data['drivers'][driver]['driver_name'] = driver_connection[0]
            # Controllers will be a list under the driver key
            data['drivers'][driver]['controllers'] = []

            # NOTE: Driver controllers are pose controls. These are the controls
            #       with stored values to put the rig into the pose the shape was made for.

            # Is a driver controller connected, could be any number of them
            controllers = mc.listAttr(driver + '.driverController', m=True)

            # Add connected driver controllers
            if controllers:
                for ctrl in controllers:
                    plug = mc.listConnections(node + '.%s' % ctrl, p=1)
                    if not plug:
                        continue
                    plug = plug[0]
                    driver_index = common.getIndex(ctrl)
                    driver_indexes.append(driver_index)
                    plug = str(plug)
                    data['drivers'][driver]['controllers'].append(plug)

            # twistAxis
            value = mc.getAttr(driver+'.driverTwistAxis')
            data['drivers'][driver]['driverTwistAxis'] = value
            # eulerTwist
            value = mc.getAttr(driver+'.driverEulerTwist')
            data['drivers'][driver]['driverEulerTwist'] = value

        # Poses is a order dict that will hold all individual pose data
        data['poses'] = OrderedDict()

        # Get poses - This could have potential index gaps if poses have been deleted
        #             So this attr and index will be used to query but a gapless index
        #             order will be written to the file.
        #
        #             WARNING: Not sure if this new index order will match
        #                      up with the other interp data
        #
        poses = mc.ls('%s.pose[*]' % node)

        i = 0
        for pose in poses:

            # Pose export is the pose attribute at the index that will avoid gaps
            pose_export = '{}.pose[{}]'.format(node, i)

            # pose_export attribute will be a ordered dict under the poses key
            data['poses'][pose_export] = OrderedDict()

            # Controllers
            data['poses'][pose_export]['controllers'] = OrderedDict()

            # Driver indexes are populated in the previous drivers loop
            data_attr = pose + '.poseControllerData[0]' + '.poseControllerDataItem[*]'
            dataItems = mc.ls(data_attr)

            for di in dataItems:

                # Replace the pose attr with the pose_export attr to ensure there are no index gaps
                # that may have happened if poses where deleted in the scene and new ones added.
                #
                di_export = di.replace(pose, pose_export)

                diDict = OrderedDict()
                diDict['name'] = mc.getAttr(di + '.poseControllerDataItemName')
                diDict['type'] = mc.getAttr(di + '.poseControllerDataItemType')
                diDict['value'] = mc.getAttr(di + '.poseControllerDataItemValue')
                data['poses'][pose_export]['controllers'][di_export] = diDict

            # Settings
            attrs = [
                'poseName',
                'isEnabled',
                'poseType',
                'isIndependent',
                'poseFalloff',
                'poseRotationFalloff',
                'poseTranslationFalloff'
                ]
            for attr in attrs:
                value = mc.getAttr(pose+'.'+attr)
                data['poses'][pose_export][attr] = value
            attrs = [
                'poseTranslation',
                'poseRotation'
                ]
            for attr in attrs:
                data['poses'][pose_export][attr] = OrderedDict()
                for index, node_attr in enumerate(mc.ls('{}.{}[*]'.format(pose, attr))):
                    value = mc.getAttr(node_attr)
                    data['poses'][pose_export][attr]['{}.{}[{}]'.format(pose_export, attr, index)] = value
            # Drivens
            poseIndex = common.getIndex(pose)
            attr = '{}.output[{}]'.format(node, poseIndex)
            export_attr = '{}.output[{}]'.format(node, i)
            data['poses'][pose_export]['driver_attr'] = export_attr
            if mc.objExists(attr):
                drivens = mc.listConnections(attr, p=1)
                data['poses'][pose_export]['drivens'] = drivens

            i += 1

        self._data[node].update(data)

    def applyData(self, nodes, mirror=False):
        """
        """
        for poseInterp in nodes:
            if not poseInterp in self._data:
                print('psd load: missing poseInterp', poseInterp)
                continue
            # Driver controller - per interp
            #
            if not mc.objExists('{}.enabled'.format(poseInterp)):
                mc.addAttr(poseInterp, ln='enabled', at='bool', dv=True)
            if self._data[poseInterp].has_key('isEnabled'):
                mc.setAttr('{}.enabled'.format(poseInterp), self._data[poseInterp]['isEnabled'])
            if self._data[poseInterp].has_key('drivers'):
                for driver in self._data[poseInterp]['drivers'].keys():
                    if self._data[poseInterp]['drivers'][driver].has_key('driver_name'):
                        driver_name = self._data[poseInterp]['drivers'][driver]['driver_name']
                        if not mc.objExists(driver_name):
                            continue
                        # make the basic connections that are required for the drivers
                        connection = mc.listConnections('{}.driverMatrix'.format(driver)) or list()
                        if not driver_name in connection:
                            mc.connectAttr('{}.matrix'.format(driver_name),
                                           '{}.driverMatrix'.format(driver), f=True)
                        if mc.nodeType(driver_name) == 'joint':
                            connection = mc.listConnections('{}.driverOrient'.format(driver)) or list()
                            if not driver_name in connection:
                                mc.connectAttr('{}.jointOrient'.format(driver_name),
                                               '{}.driverOrient'.format(driver), f=True)
                        connection = mc.listConnections('{}.driverRotateAxis'.format(driver)) or list()
                        if not driver_name in connection:
                            mc.connectAttr('{}.rotateAxis'.format(driver_name),
                                           '{}.driverRotateAxis'.format(driver), f=True)
                        connection = mc.listConnections('{}.driverRotateOrder'.format(driver)) or list()
                        if not driver_name in connection:
                            mc.connectAttr('{}.rotateOrder'.format(driver_name),
                                           '{}.driverRotateOrder'.format(driver), f=True)

                    mc.setAttr('{}.driverTwistAxis'.format(driver),
                               self._data[poseInterp]['drivers'][driver]['driverTwistAxis'])
                    mc.setAttr('{}.driverEulerTwist'.format(driver),
                               self._data[poseInterp]['drivers'][driver]['driverEulerTwist'])
                    ctrlrs = self._data[poseInterp]['drivers'][driver]['controllers']
                    for ctrl in ctrlrs:
                        index = ctrlrs.index(ctrl)
                        try:
                            mc.connectAttr(ctrl, driver + '.driverController[%s]' % index, f=1)
                        except:
                            pass

            attr_list = ['regularization', 'outputSmoothing', 'interpolation',
                         'allowNegativeWeights', 'enableRotation', 'enableTranslation']
            # loop through the attr list and store the value
            for attr in attr_list:
                if self._data[poseInterp].has_key(attr):
                    mc.setAttr('{}.{}'.format(poseInterp, attr), self._data[poseInterp][attr])

            # Pose controllers - per pose
            #
            i = 0
            for pose in self._data[poseInterp]['poses'].keys():
                rig_psd.addPose(poseInterp, self._data[poseInterp]['poses'][pose]['poseName'])
                dataItems = self._data[poseInterp]['poses'][pose]['controllers'].keys()
                driven_list = self._data[poseInterp]['poses'][pose]['drivens'] or []
                for driven in driven_list:
                    if mc.objExists(driven) and self._data[poseInterp]['poses'][pose].has_key('driver_attr'):
                        mc.connectAttr(self._data[poseInterp]['poses'][pose]['driver_attr'], driven, f=True)
                i += 1
                for item in dataItems:
                    name = self._data[poseInterp]['poses'][pose]['controllers'][item]['name']
                    ptype = self._data[poseInterp]['poses'][pose]['controllers'][item]['type']
                    value = self._data[poseInterp]['poses'][pose]['controllers'][item]['value']
                    if isinstance(value, list):
                        value = value[0]
                    try:
                        mc.setAttr(item + '.poseControllerDataItemName', name, type='string')
                        mc.setAttr(item + '.poseControllerDataItemType', ptype)
                        if isinstance(value, tuple) or isinstance(value, list):
                            mc.setAttr(item + '.poseControllerDataItemValue', *value, type='double3')
                        else:
                            mc.setAttr(item + '.poseControllerDataItemValue', value)
                    except:
                        print('it did not work!')
                attrs = [
                    'isEnabled',
                    'poseType',
                    'isIndependent',
                    'poseFalloff',
                    'poseRotationFalloff',
                    'poseTranslationFalloff'
                ]
                for attr in attrs:
                    if self._data[poseInterp]['poses'][pose].has_key(attr):
                        try:
                            mc.setAttr(pose + '.' + attr, self._data[poseInterp]['poses'][pose][attr])
                        except:
                            traceback.print_exc()

                attrs = [
                    'poseTranslation',
                    'poseRotation'
                ]
                for attr in attrs:
                    if self._data[poseInterp]['poses'][pose].has_key(attr):
                        for node_attr in self._data[poseInterp]['poses'][pose][attr].keys():
                            mc.setAttr(node_attr, self._data[poseInterp]['poses'][pose][attr][node_attr], type='doubleArray')
