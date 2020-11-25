"""attribute functions"""
import maya.cmds as mc
import maya.mel as mm
import maya.api.OpenMaya as om2
import showtools.maya.common as common

TRANSLATE = ['tx', 'ty', 'tz']
ROTATE = ['rx', 'ry', 'rz']
SCALE = ['sx', 'sy', 'sz']
TRANSFORMS = TRANSLATE + ROTATE + SCALE
USER = lambda node: map(str, [a for a in mc.listAttr(node, ud=True) or [] if '.' not in a])
KEYABLE = lambda node: map(str, [a for a in mc.listAttr(node, k=True) or [] if '.' not in a])
NONKEYABLE = lambda node: map(str, [a for a in mc.listAttr(node, cb=True) or [] if '.' not in a])
CHANNELBOX = lambda node: KEYABLE(node) + NONKEYABLE(node)
CONNECTABLE = lambda node: map(str, [a for a in mc.listAttr(node, sa=True) or [] if '.' not in a])
ALL = lambda node: map(str, [a for a in mc.listAttr(node) or [] if '.' not in a])

ANIM = ['animCurveTL', 'animCurveTA', 'animCurveTT', 'animCurveTU']
DRIVEN = ['animCurveUL', 'animCurveUA', 'animCurveUT', 'animCurveUU']


def divider(node, label, aboveAttr=None, character='~', repeat=16):
    """Adds a divider attribute to the node.  The divider attribute is a enum style attr with the
    nice name set to be a repeating character to act as a visual divider.  The first item of the
    enum attr is set to the provided label.

    If an attribute is given for the "aboveAttr" argument the divider will be arranged above it.
    Otherwise it will be placed at the bottom of the user defined attribute stack.

    :param node: Maya node name
    :type node: str

    :param label: name of the first enum item to serve as a label
    :type label: str

    :param aboveAttr: if an attr is given here the divider will be place above it
    :type aboveAttr: str

    :param character: the character to be repeated as a visual divider (default "~")
    :type character: str

    :param repeat: number to times to repeat the given character
    :type repeat: int
    """
    # get divider attribute number
    existing = [str(d) for d in mc.listAttr(node, ud=True) or [] if d.startswith('div')]
    div = 'div'+str(len(existing))

    # add divider
    mc.addAttr(node, ln=div, nn=(character*repeat), at='enum', en=label)
    mc.setAttr(node + '.' + div, l=True, cb=True)

    # arrange divider
    if aboveAttr:
        arrangeToAttr(node=node, attr=div, destination=aboveAttr, after=False)

    return node + '.' + div


def arrangeToAttr(node, attr, destination, after=False):
    """Arrange a user-defined attribute among other user defined attributes.

    Arranging uses the delete/undo method since Maya doesn't support attribute reordering. Deleting
    and undoing an attribute sends it to the bottom of the list.  It is a silly way to do it, but
    it is more convenient than deleting and recreating with preserved connections.

    This action is NOT undoable.

    :param node: Maya node name
    :type node: str

    :param attr: Maya node attribute
    :type attr: str

    :param destination: destination attribute to arrange attr beside
    :type destination: str

    :param after: whether to place attribute before or after the destination attr
    :type after: bool
    """
    # get attributes to arrange
    udAttrs = mc.listAttr(node, ud=True)
    udAttrs.pop(udAttrs.index(attr))

    # check destination attr
    if destination not in udAttrs:
        raise Exception('Destination attribute is not user defined. Cannot arrange around it.')

    # get destination index
    destIndex = udAttrs.index(destination)
    if after:
        destIndex += 1

    # build final list of attrs - trimmed to only affect attrs after the destination attr.
    udAttrs.insert(destIndex, attr)
    attrs = udAttrs[destIndex:]

    # unlock attributes
    locked = [a for a in mc.listAttr(node, ud=True, l=True) or [] if a in attrs]
    if locked:
        for attr in locked:
            mc.setAttr(node+'.'+attr, l=False)

    # arrange attributes
    for attr in attrs:
        mc.deleteAttr(node, at=attr)
        mc.undo()

    # relock attributes
    if locked:
        for attr in locked:
            mc.setAttr(node+'.'+attr, l=True)


def arrangeToTop(node, attr):
    """Arrange given attribute to the top of the user defined attribute stack.

    :param node: Maya node name
    :type node: str

    :param attr: Maya node attribute
    :type attr: str
    """
    # get user defined attributes
    udAttrs = mc.listAttr(node, ud=True)

    # arrange
    arrangeToAttr(node=node, attr=attr, destination=udAttrs[0], after=False)


def arrangeToBottom(node, attr):
    """Arrange given attribute to the bottom of the user defined attribute stack.

    :param node: Maya node name
    :type node: str

    :param attr: Maya node attribute
    :type attr: str
    """
    # unlock attributes
    locked = False
    if mc.getAttr(node+'.'+attr, l=True):
        mc.setAttr(node+'.'+attr, l=False)
        locked = True

    # arrange attribute
    mc.deleteAttr(node, at=attr)
    mc.undo()

    # relock attributes
    if locked:
        mc.setAttr(node+'.'+attr, l=True)


def arrangeSlide(node, attr, up=True):
    """Slide the given attribute up or down in the user defined attribute stack.

    :param node: Maya node name
    :type node: str

    :param attr: Maya node attribute
    :type attr: str

    :param up: direction to slide the attribute in the stack. (False=down)
    :type up: bool
    """
    # get user defined attributes
    udAttrs = mc.listAttr(node, ud=True, k=True)

    # get destination attr
    attrIndex = udAttrs.index(attr)
    if attrIndex is 0 and up is True:
        # attr is already at the top, do nothing
        return
    elif attrIndex is len(udAttrs)-1 and up is False:
        # attr is already at the bottom, do nothing
        return
    else:
        # attr can be arranged
        if up:
            # slide up
            destAttr = udAttrs[attrIndex-1]
            arrangeToAttr(node=node, attr=attr, destination=destAttr, after=False)
        else:
            # slide down
            destAttr = udAttrs[attrIndex+1]
            arrangeToAttr(node=node, attr=attr, destination=destAttr, after=True)


def blendAttributes(sourceNode, targetNode, attrs, weight=0.5):
    """Blend targetNode attributes towards sourceNode by a factor of the weight value.

    Weight values between 0 and 1 are a weighted average.  Weight values greater than 1 are a
    multiplier on the weighted average.  For example a weight value of 2.0 will double the
    difference between the two attributes.  Negative weight values are not supported.

    :param sourceNode: node to weight towards
    :type sourceNode: str

    :param targetNode: node to apply weight to
    :type targetNode: str

    :param attrs: list of attribute names core between source and target
    :type attrs: list

    :param weight: blending weight (default 0.5)
    :type weight: float
    """
    if attrs:
        sourceAttrs = [sourceNode+'.'+a for a in attrs]
        targetAttrs = [targetNode+'.'+a for a in attrs]

        # validate attrs
        for attr in sourceAttrs + targetAttrs:
            # exists
            if not mc.objExists(attr):
                raise Exception('Attribute not found "%s"' % attr)

            # blendable type
            attr_type = mc.getAttr(attr, type=True)
            if attr_type in ['enum', 'bool']:
                mc.warning('Attribute "{0}" of type "{1}" cannot be blended.  Skipping...'.format(attr, attr_type))
                if attr in sourceAttrs: sourceAttrs.remove(attr)
                if attr in targetAttrs: targetAttrs.remove(attr)
    else:
        # get numeric attributes for source and target
        sourceAttrs = [sourceNode+'.'+a for a in mc.listAttr(sourceNode, k=True, v=True, lf=True, scalar=True)]
        for attr in sourceAttrs:
            if mc.getAttr(attr, type=True) in ['enum', 'bool']:
                sourceAttrs.remove(attr)

        targetAttrs = [targetNode+'.'+a for a in mc.listAttr(targetNode, k=True, v=True, lf=True, scalar=True)]
        for attr in targetAttrs:
            if mc.getAttr(attr, type=True) in ['enum', 'bool']:
                targetAttrs.remove(attr)

    # blend attrs
    for sourceAttr, targetAttr in zip(sourceAttrs, targetAttrs):
        # get current values
        sourceValue = mc.getAttr(sourceAttr)
        targetValue = mc.getAttr(targetAttr)

        # get weighted value
        weightedValue = targetValue
        if weight <= 1:
            weightedValue = (sourceValue*weight)+(targetValue*(1-weight))
        elif weight > 1:
            weightedValue = ((sourceValue*weight)+(targetValue*(1-weight)))*weight
        else:
            raise Exception('Function accepts positive percentages only.')

        # apply weighted value
        mc.setAttr(targetAttr, weightedValue, clamp=True)


def lockAndHideAttrs(nodes, attrs):
    """Locks and hides given attributes.

    :param nodes: list of Maya nodes (can also accept single node str)
    :type nodes: list | str

    :param attrs: list of Maya attributes to lock and hide (can also accept single attr str)
    :type attrs: list | str
    """
    # get node list
    if isinstance(nodes, str):
        nodes = [nodes]

    # get attr list
    if isinstance(attrs, str):
        attrs = [attrs]

    # lock and hide attrs
    for node in nodes:
        for attr in attrs:
            mc.setAttr(node+'.'+attr, lock=True, keyable=False, channelBox=False)


def lock(node, attr):
    '''
    lock attributes

    :param node: Attribute parent node
    :type node: str | list

    :param attr: Attribute name(s) or path(s)
    :type attr: str or list
    '''
    nodeList = common.toList(node)
    attrList = common.toList(attr)

    for node in nodeList:
        for attr in attrList:  
            mc.setAttr("{0}.{1}".format(node,attr), lock=True)


def hide(node, attr):
    '''
    hide attributes

    :param node: Attribute parent node
    :type node: str | list

    :param attr: Attribute name(s) or path(s)
    :type attr: str or list
    '''
    nodeList = common.toList(node)
    attrList = common.toList(attr)

    for node in nodeList:
        for attr in attrList:  
            mc.setAttr("{0}.{1}".format(node,attr), keyable=False, cb=False)


def lockAndHide(node, attr):
    '''
    lock and hide attributes

    :param node: Attribute parent node
    :type node: str | list

    :param attr: Attribute name(s) or path(s)
    :type attr: str or list
    '''
    lock(node, attr)
    hide(node, attr)


def unlock(node, attr):
    '''
    unlock attributes

    :param node: Attribute parent node
    :type node: str | list

    :param attr: Attribute name(s) or path(s)
    :type attr: str or list
    '''
    nodeList = common.toList(node)
    attrList = common.toList(attr)

    #lock attributes
    for node in nodeList:
        for attr in attrList:
            mc.setAttr("{0}.{1}".format(node,attr), l = False)


def unhide(node, attr):     
    '''
    unhide attributes

    :param node: Attribute parent node
    :type node: str | list

    :param attr: Attribute name(s) or path(s)
    :type attr: str or list
    '''

    nodeList = common.toList(node)
    attrList = common.toList(attr)

    #lock attributes
    for node in nodeList:
        for attr in attrList:
            mc.setAttr("{0}.{1}".format(node,attr), k=True, cb=True)    
            mc.setAttr("{0}.{1}".format(node,attr), k=True)


def unlockAndUnhide(attr, node):
    '''
    unlock and unhide attributes

    :param node: Attribute parent node
    :type node: str | list

    :param attr: Attribute name(s) or path(s)
    :type attr: str or list

    '''
    unlock(attr, node)
    unhide(attr,node)


def setKeyableAttrs(nodes, attrs):
    """Sets supplied attrs as keyable, and locks and hides all others.

    Consider using attr globals like TRANSFORM, TRANSLATE, ROTATE, and SCALE.

    :param nodes: list of Maya nodes (can also accept single node str)
    :type nodes: list | str

    :param attrs: list of Maya attributes to lock and hide (can also accept single attr str)
    :type attrs: list | str
    """
    # get node list
    if not isinstance(nodes, list):
        nodes = [nodes]

    # get attr list
    if not isinstance(attrs, list):
        attrs = [attrs]

    # set keyable
    for node in nodes:
        # lock and hide all attrs
        lockAndHide_attrs = list()
        keyable_attrs = mc.listAttr(node, keyable=True)
        channelBox_attrs = mc.listAttr(node, channelBox=True)
        if keyable_attrs:
            lockAndHide_attrs.extend(keyable_attrs)
        if channelBox_attrs:
            lockAndHide_attrs.extend(channelBox_attrs)

        for attr in lockAndHide_attrs:
            mc.setAttr(
                node+'.'+attr, lock=True, keyable=False, channelBox=False)

        # unlock and unhide keyable attrs
        for attr in attrs:
            mc.setAttr(node+'.'+attr, lock=False, keyable=True)


def setAttrs(nodes, attrs, value):
    """
    Set the value for all provided attrs on all provided nodes. If the node does not exist, or if
    the attribute does not exist on the node a warning is given.

    :param nodes: list of Maya nodes (can also accept single node str)
    :type nodes: list | str

    :param attrs: list of Maya attributes to lock and hide (can also accept single attr str)
    :type attrs: list | str

    :param value:
    :type value: any

    :return:
    """
    # cast nodes as list
    if not isinstance(nodes, list):
        nodes = [nodes]
    if not isinstance(attrs, list):
        attrs = [attrs]

    # set attrs
    for node in nodes:
        for attr in attrs:
            plug = node + '.' + attr
            setPlugValue(plug=plug, value=value)


def getAnimatedAttrs(node, anim=True, driven=True):
    animated = list()
    for attr in ALL(node):
        nodeAttr = node + '.' + attr
        connections = mc.listConnections(nodeAttr, s=True, d=False)
        if connections:
            for connection in connections:
                cTypes = list()
                cTypes.extend(DRIVEN if driven else [])
                cTypes.extend(ANIM if anim else [])
                if mc.nodeType(connection) in cTypes:
                    animated.append(attr)
    return animated


def _getPlug(plug):
    """Returns MPlug object for the given Maya plug name.

    :param plug: plug string (node.attr) to return MPlug for
    :type plug: str

    :returns: MPlug object
    :rtype: OpenMaya.MPlug
    """
    # get node and attr from plug string
    parts = plug.split('.')
    node = parts[0]
    attr = '.'.join(parts[1:])
    baseAttr = parts[1].split('[')[0]

    # get node function set
    selList = om2.MSelectionList()
    selList.add(node)
    nodeObject = selList.getDependNode(0)
    nodeFn = om2.MFnDependencyNode(nodeObject)

    # get plug
    if len(parts) > 2 or '[' in attr:
        # compound attrs
        if nodeFn.hasAttribute(baseAttr):

            # child plugs iterator
            def _getChildPlugs(p):
                a = p.attribute()
                apiType = a.apiType()
                childPlugs.append(p)
                if p.isArray:
                    if apiType == om2.MFn.kTypedAttribute:
                        for i in xrange(p.numElements()):
                            cp = p.elementByLogicalIndex(i)
                            _getChildPlugs(cp)
                    elif apiType == om2.MFn.kMessageAttribute:
                        childPlugs.append(p)
                    else:
                        numChildren = int()
                        try:
                            numChildren = p.numElements()
                        except TypeError:
                            pass
                        try:
                            numChildren = p.numChildren()
                        except TypeError:
                            pass
                        for i in xrange(numChildren):
                            cp = om2.MPlug(p.elementByLogicalIndex(i))
                            _getChildPlugs(cp)
                elif p.isCompound:
                    for i in xrange(p.numChildren()):
                        cp = p.child(i)
                        _getChildPlugs(cp)

            # get child plugs
            childPlugs = list()
            basePlug = nodeFn.findPlug(baseAttr, True)
            _getChildPlugs(basePlug)

            for childPlug in childPlugs:
                if childPlug.name().partition('.')[-1] == attr:
                    return childPlug
    else:
        # simple attrs
        if nodeFn.hasAttribute(attr):
            return nodeFn.findPlug(attr, True)

    mc.warning('Plug "%s" could not be found.' % plug)
    return


def getPlugValue(plug):
    """Returns the value(s) for the given plug.

    :param plug: plug as string (node.attr) or MPlug
    :type plug: str | MPlug

    :returns: value of attribute derived through api
    :rtype: variable
    """
    # get plug from attr if not MPlugs
    if not type(plug) == om2.MPlug:
        plug = _getPlug(plug)

    if not plug:
        print 'Plug not found.'
        return

    attr = plug.attribute()
    apiType = attr.apiType()

    # Float Groups - rotate, translate, scale
    # Multis
    # Compounds
    if apiType in [om2.MFn.kAttribute3Double, om2.MFn.kAttribute3Float, om2.MFn.kCompoundAttribute]:
        result = list()
        if plug.isArray:
            for i in xrange(plug.numChildren()):
                plug.selectAncestorLogicalIndex(i, attr)
                result.append(getPlugValue(plug))
        elif plug.isCompound:
            for c in xrange(plug.numChildren()):
                result.append(getPlugValue(plug.child(c)))
        return result

    # Distance
    elif apiType in [om2.MFn.kDoubleLinearAttribute, om2.MFn.kFloatLinearAttribute]:
        return plug.asMDistance().asCentimeters()

    # Angle
    elif apiType in [om2.MFn.kDoubleAngleAttribute, om2.MFn.kFloatAngleAttribute]:
        return plug.asMAngle().asDegrees()

    # TYPED
    elif apiType == om2.MFn.kTypedAttribute:
        pType = om2.MFnTypedAttribute(attr).attrType()
        # Matrix
        if pType == om2.MFnData.kMatrix:
            matrixFn = om2.MFnMatrixData (plug.asMObject())
            result = None
            try:
                m = list(matrixFn.matrix())
                result = [m[0:4], m[4:8], m[8:12], m[12:16]]
            except:
                pass
            return result
        # String
        elif pType == om2.MFnData.kString:
            return str(plug.asString())

    # MATRIX
    elif apiType == om2.MFn.kMatrixAttribute:
        return om2.MFnMatrixData(plug.asMObject()).matrix()

    # NUMBERS
    elif apiType == om2.MFn.kNumericAttribute:
        pType = om2.MFnNumericAttribute(attr).numericType()
        if pType == om2.MFnNumericData.kBoolean:
            return plug.asBool()
        elif pType in [om2.MFnNumericData.kShort, om2.MFnNumericData.kInt, om2.MFnNumericData.kLong, om2.MFnNumericData.kByte]:
            return plug.asInt()
        elif pType in [om2.MFnNumericData.kFloat, om2.MFnNumericData.kDouble, om2.MFnNumericData.kAddr]:
            return plug.asDouble()

    # Enum
    elif apiType == om2.MFn.kEnumAttribute:
        return plug.asInt()


def setPlugValue(plug, value):
    """Utility function to set an attribute with the given value.  Assume reasonable values given
    from a getAttr function.  Supply errors for values that are in no way settable for the given
    attribute.

    Example: If attr is float3 and value is int, int will be applied to all 3 float values but a
    string would be unable to be assigned.

    :param plug: plug as string (node.attr) or MPlug
    :type plug: str | MPlug

    :param value: Input value to set attribute
    :type value: variable

    :returns: Plug and set value
    :rtype: str
    """
    # get plug from attr if not MPlugs
    if not type(plug) == om2.MPlug:
        plug = _getPlug(plug)

    if not plug:
        print 'Plug not found.'
        return

    attr = plug.attribute()
    apiType = attr.apiType()

    # Float Groups - rotate, translate, scale
    if apiType in [om2.MFn.kAttribute3Double, om2.MFn.kAttribute3Float]:
        result = []
        if plug.isCompound:
            if isinstance(value, list):
                for c in xrange(plug.numChildren()):
                    result.append(setPlugValue(plug.child(c), value[c]))
                return result
            elif type(value) == om2.MEulerRotation:
                setPlugValue(plug.child(0), value.x)
                setPlugValue(plug.child(1), value.y)
                setPlugValue(plug.child(2), value.z)
            else:
                raise ValueError('Value ({1}) is {2}. {0} needs type list.'.format(plug.info, value, type(value)))

    # Distance
    elif apiType in [om2.MFn.kDoubleLinearAttribute, om2.MFn.kFloatLinearAttribute]:
        if isinstance(value, float):
            value = om2.MDistance(value, om2.MDistance.kCentimeters)
            plug.setMDistance(value)
        else:
            raise ValueError('Value ({1}) is {2}. {0} needs  type float.'.format(plug.info, value, type(value)))

    # Angle
    elif apiType in [om2.MFn.kDoubleAngleAttribute, om2.MFn.kFloatAngleAttribute]:
        if isinstance(value, float):
            value = om2.MAngle(value, om2.MAngle.kDegrees)
            plug.setMAngle(value)
        else:
            raise ValueError('Value ({1}) is {2}. {0} needs type float.'.format(plug.info, value, type(value)))

    # Typed - matrix must be handled later as MPlug
    elif apiType == om2.MFn.kTypedAttribute:
        pType = om2.MFnTypedAttribute(attr).attrType()
        if pType == om2.MFnData.kMatrix:
            if isinstance(value, om2.MPlug):
                pass
            else:
                plug_node = plug.node()
                MFnTrans = om2.MFnTransform(plug_node)
                sourceMatrix = om2.MTransformationMatrix(value)
                MFnTrans.set(sourceMatrix)
        # String
        elif pType == om2.MFnData.kString:
            plug.setString(value)

    # MATRIX
    elif apiType == om2.MFn.kMatrixAttribute:
        if isinstance(value, om2.MPlug):
            # value must be an MPlug
            sourceValueAsMObject = om2.MFnMatrixData(value.asMObject()).object()
            plug.setMObject(sourceValueAsMObject)
        else:
            raise ValueError('Value is not an MPlug. To set a MMatrix both variables must be MPlugs.')

    # Numbers
    elif apiType == om2.MFn.kNumericAttribute:
        pType = om2.MFnNumericAttribute(attr).numericType()
        if pType == om2.MFnNumericData.kBoolean:
            if isinstance(value, bool):
                plug.setBool(value)
            else:
                raise ValueError('Value ({1}) is {2}. {0} needs type bool.'.format(plug.info, value, type(value)))
        elif pType in [om2.MFnNumericData.kShort, om2.MFnNumericData.kInt, om2.MFnNumericData.kLong, om2.MFnNumericData.kByte]:
            if isinstance(value, int):
                plug.setInt(value)
            else:
                raise ValueError('Value ({1}) is {2}. {0} needs type int.'.format(plug.info, value, type(value)))
        elif pType in [om2.MFnNumericData.kFloat, om2.MFnNumericData.kDouble, om2.MFnNumericData.kAddr]:
            if isinstance(value, float):
                plug.setDouble(value)
            else:
                raise ValueError('Value ({1}) is {2}. {0} needs type float.'.format(plug.info, value, type(value)))

    # Enums
    elif apiType == om2.MFn.kEnumAttribute:
        plug.setInt(value)

    return '{0} was set to {1}'.format(plug.info, value)


def getLeafAttrs(node, attrs):
    """Returns the leaf attributes under the given attrs. The given attrs maybe parents of all types
    (compound, array, multi, etc.). If the given attribute name is already a leaf it is returned.
    
    :param node: node name to get leaf attrs for
    :type node: str
    
    :param attrs: attribute names to combine with node to get plugs
    :type attrs str | list
    
    :returns: list of leaf attribute names
    :rtype: list
    """
    leafAttrs = list()
    
    # child attrs iterator
    def _getChildAttrs(plug):
        attr = plug.attribute()
        apiType = attr.apiType()
        if plug.isArray:
            if apiType == om2.MFn.kTypedAttribute:
                for i in xrange(plug.numElements()):
                    childPlug = plug.elementByLogicalIndex(i)
                    _getChildAttrs(childPlug)
            elif apiType == om2.MFn.kMessageAttribute:
                attrName = plug.name().partition('.')[-1]
                leafAttrs.append(str(attrName))
            else:
                numChildren = int()
                try:
                    numChildren = plug.numElements()
                except TypeError:
                    pass
                try:
                    numChildren = plug.numChildren()
                except TypeError:
                    pass
                for i in xrange(numChildren):
                    childPlug = om2.MPlug(plug.elementByLogicalIndex(i))
                    _getChildAttrs(childPlug)
        elif plug.isCompound:
            for c in xrange(plug.numChildren()):
                _getChildAttrs(plug.child(c))
        else:
            attrName = plug.name().partition('.')[-1]
            leafAttrs.append(str(attrName))
    
    # check node
    if not mc.objExists(node):
        mc.warning('Object does not exist "%s"' % node)
        return
    
    # get leaf attrs
    if not isinstance(attrs, list): attrs = [attrs]
    for attr in attrs:
        # check that attribute exists on the node or it's shape
        if not mc.objExists(node + '.' + attr):
            if mc.nodeType(node) == 'transform':
                shapes = mc.listRelatives(node, s=True)
                if shapes:
                    if mc.objExists(shapes[0] + '.' + attr):
                        node = shapes[0]
        if not mc.objExists(node + '.' + attr):
            mc.warning('Attribute not found "%s.%s"' % (node, attr))
            return leafAttrs
        
        # get child attrs
        plug = _getPlug(node + '.' + attr)
        if plug:
            _getChildAttrs(plug)
        else:
            mc.warning('Attribute not found "%s.%s"' % (node, attr))
    
    return leafAttrs


def getAddAttrCmds(attrs):
    """Get proper MEL commands to add an attribute.
    
    Provided attributes are expected in node.attr format.
    
    Commands are returned as a list of tuples.
      [(node, cmd), (node, cmd), (node, cmd), ...]
    
    This format is expected by the companion function applyAddAttrCmds.
    
    :param attrs: list of attrs in node.attr format
    :type attrs: list | str

    :returns: list of (node, cmd) tuples
    :rtype: list
    """
    # check plugin
    if not mc.pluginInfo('mayaGetAttrCmdsCmd', q=True, loaded=True):
        mc.loadPlugin('mayaGetAttrCmdsCmd')

    # check attrs
    if not isinstance(attrs, list): attrs = [attrs]
    
    # get commands
    commands = list()
    for attr in attrs:
        # get node name
        node = attr.split('.')[0]
        
        # get command
        cmd = str(mc.getAddAttrCmds(attr)[0])
        commands.append((node, cmd))

    return commands


def getSetAttrCmds(attrs):
    """Get proper MEL commands to set an attribute.
    
    Provided attributes are expected in node.attr format.
    
    Commands are returned as a list of tuples.
      [(node, cmd), (node, cmd), (node, cmd), ...]
    
    This format is expected by the companion function applySetAttrCmds.
    
    :param attrs: list of attrs in node.attr format
    :type attrs: list | str

    :returns: list of (node, cmd) tuples
    :rtype: list
    """
    # check plugin
    if not mc.pluginInfo('mayaGetAttrCmdsCmd', q=True, loaded=True):
        mc.loadPlugin('mayaGetAttrCmdsCmd')
    
    # check attrs
    if not isinstance(attrs, list): attrs = [attrs]
    
    # get commands
    commands = list()
    for attr in attrs:
        # get node name
        node = attr.split('.')[0]
        
        # get command
        cmd = mc.getSetAttrCmds(attr)
        if cmd: cmd = str(''.join(cmd))
        commands.append((node, cmd))
        
    return commands


def applyAddAttrCmds(cmds, targetNode=None):
    """Execute the MEL addAttr commands stored in the provided cmds list.
    
    The expected input comes from the companion getAddAttrCmds function.
      [(node, cmd), (node, cmd), (node, cmd), ...]
    
    Use the targetNode argument to redirect the addAttr commands to a new node
    instead of the one stored with each tuple in the list.
    
    :param cmds: list of (node, cmd) commands
    :type cmds: list
    
    :param targetNode: add attrs to this node instead
    :type targetNode: str | None
    """
    # apply commands
    for cmd in cmds:
        # unpack node and command
        node = targetNode or cmd[0]
        cmd = cmd[1]
        
        # get attr name from cmd string
        attr = cmd.split('-longName')[1].split('"')[1]
        
        # format command - add name of node to the end of command
        cmd = cmd.replace(';', (' "%s";' % node))
        
        # add attr
        if not mc.objExists(node+'.'+attr):
            mm.eval(cmd)


def applySetAttrCmds(cmds, targetNode=None):
    """Execute the MEL setAttr commands stored in the provided cmds list.
    
    The expected input comes from the companion getSetAttrCmds function.
      [(node, cmd), (node, cmd), (node, cmd), ...]
    
    Use the targetNode argument to redirect the setAttr commands to a new node
    instead of the one stored with each tuple in the list.
    
    :param cmds: list of (node, cmd) commands
    :type cmds: list
    
    :param targetNode: add attrs to this node instead
    :type targetNode: str | None
    """
    # apply commands
    for cmd in cmds:
        # unpack node and command
        node = targetNode or cmd[0]
        cmd = cmd[1]

        # depending on the attr type it might not have a setAttr command
        if not cmd:
            continue
        
        # get attr name from cmd string
        attr = cmd.split('".')[1].split('"')[0]
        
        # format command - add name of node to the end of command
        cmd = cmd.replace('.'+attr, node+'.'+attr)

        # set attr
        if mc.objExists(node+'.'+attr) and mc.getAttr(node+'.'+attr, settable=True):
            try:
                attrType = mc.getAttr(node+'.'+attr, type=True)
            except:
                continue
            
            if attrType == 'message':
                continue

            try:
                mm.eval(cmd)
            except:
                pass


def rmanGetAttrName(attr):
    """Helper to run MEL rmanGetAttrName command

    :param attr: Attribute to get renderman name of
    :type attr: str

    :returns: returns the renderman equivalent name for the given attribute
    :rtype: str
    """
    return mm.eval('rmanGetAttrName {0}'.format(attr))


def rmanAddAttr(node, attr, val):
    """Helper to run MEL rmanAddAttr command, generally to be used with
    rmanGetAttrName

    :param node: Node to add attribute to
    :type node: str

    :param attr: Attribute to add
    :type attr: str

    :param value: Set value of attribute
    :type attr: str

    :returns: added attr
    :rtype: str
    """
    return mm.eval('rmanAddAttr {0} {1} {2}'.format(node, attr, val))


def rmanSetAttr(node, attr, val):
    """Helper to run MEL rmanSetAttr command, generally to be used with
    rmanGetAttrName

    :param node: Node to add attribute to
    :type node: str

    :param attr: Attribute to add
    :type attr: str

    :param value: Set value of attribute
    :type attr: str

    :returns: added attr
    :rtype: str
    """
    return mm.eval('rmanSetAtr {0} {1} {2}'.format(node, attr, val))


def getRmanAttrs(node):
    """Get all node attributes created by renderman

    :param node: Input node
    :type node: str

    :returns: List of renderman attributes
    :rtype: list[str]
    """
    # get all node attr
    attrs = mc.listAttr(node)
    # extend to shapes
    shapes = mc.listRelatives(node, shapes=True)
    for shape in shapes:
        attrs = attrs + mc.listAttr(shape)

    # filter for rman
    return [x for x in attrs if 'rman' in x]

def get_selected_main_channel_box():
    '''
    Return channels that are selected in the channelbox
    '''
    if not mc.ls(sl=True):
        return
    main_cb = mm.eval('$__temp=$gChannelBoxName')
    sma = mc.channelBox(main_cb, query=True, sma=True)
    ssa = mc.channelBox(main_cb, query=True, ssa=True)
    sha = mc.channelBox(main_cb, query=True, sha=True)
    channels = list()
    if sma:
        channels.extend(sma)
    if ssa:
        channels.extend(ssa)
    if sha:
        channels.extend(sha)
    return channels

def get_resolved_attributes(control, attribute_list):
    '''
    Get all of the resolved attributes for each control that has the attributes passed and whether those
    attributes should be resolved as parent attribute names or not.

    :param control: Control that you want to resolve the attribute list for.
    :type control: str
    :param attribute_list: List of attributes you want to resolve
    :type attribute_list: list
    '''
    attribute_list = common.toList(attribute_list)
    for attr in attribute_list:
        if not mc.objExists('{}.{}'.format(control, attr)):
            continue
        parent_attr = mc.attributeQuery(attr, node=control, lp=True)
        if parent_attr:
            children_attr_list = [mc.attributeQuery(child_attr, node=control, sn=True) for child_attr in
                                  mc.attributeQuery(parent_attr, node=control, lc=True)]
            if children_attr_list:
                combine = True
                for child_attr in children_attr_list:
                    child_attr = mc.attributeQuery(child_attr, node=control, sn=True)
                    if child_attr not in attribute_list:
                        combine = False
                if combine:
                    attribute_list = list(set(attribute_list).difference(set(children_attr_list)))
                    if not parent_attr in attribute_list:
                        attribute_list.append(mc.attributeQuery(parent_attr, node=control, sn=True))

    control_attr_list = ['{}.{}'.format(control, mc.attributeQuery(attribute, node=control, ln=True)) for attribute
                         in attribute_list if mc.objExists('{}.{}'.format(control, attribute))]

    return(control_attr_list)