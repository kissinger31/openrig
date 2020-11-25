"""Rig control utilities."""
import os
from collections import OrderedDict

# maya imports
import maya.cmds as mc

# showtools imports
import openrig.maya.attr
import openrig.maya.hierarchy
import openrig.maya.transform
import openrig.shared.common
import openrig.maya.color
import openrig.maya.shader
import openrig.shared.color
import openrig.maya.curve
import openrig.maya.data.curve_data

DEBUG = False
SHAPES = ['cube', 'sphere', 'cylinder', 'circle', 'square']
CONTROLPATH = os.path.join(os.path.dirname(__file__),'controls.data')
def createControl(name, parent=None, hierarchy=None, position=None, orientation=None,
                  shape='sphere', color='blue', handle=False):
    """Builds a control object and parents it under the given parent and hierarchy.
    
    :param name: name of new control object
    :type name: str
    
    :param parent: transform to parent control to
    :type parent: str
    
    :param hierarchy: list of names to make a control hierarchy with
    :type hierarchy: list
    
    :param position: world space position for new object
    :type position: tuple | list
    
    :param orientation: orientation for new control
    :type orientation: tuple | list
    
    :param shape: shape name to create
    :type shape: str
    
    :param color: color name or RGB value tuple/list
    :type color: str | list | tuple
    
    :param handle: whether to show the displayHandle (False)
    :type handle: bool
    
    :returns: name of control
    :rtype: str
    """
    # check parent
    if parent:
        if not mc.objExists(parent):
            raise Exception('Parent object "%s" not found in scene!' % parent)
    
    # create hierarchy
    hierarchyObjects = list()
    if hierarchy:
        if isinstance(hierarchy, basestring):
            hierarchy = [hierarchy]
        if isinstance(hierarchy, tuple):
            hierarchy = list(hierarchy)
        hierarchyObjects = openrig.maya.hierarchy.create(names=hierarchy, parent=parent)
        parent = hierarchyObjects[-1]
    
    # create control
    control = mc.createNode('transform', n=name, p=parent)
    
    # position and control or hierarchy
    xformObject = hierarchyObjects[0] if hierarchyObjects else control
    position = position if position else (0.0, 0.0, 0.0)
    mc.xform(xformObject, ws=True, t=tuple(position))
    mc.makeIdentity(xformObject, apply=True, t=True)
    
    # build control shape
    if shape in SHAPES:
        createControlShape(parent=control, shape=shape, color=color)
    
    # show display handle
    if handle:
        mc.setAttr(control + '.displayHandle', True)
        if color:
            openrig.maya.color.setOverrideColor(objects=control, color=color)
    
    # add control attr
    addControlAttr(control)

    # tag as controller
    mc.controller(control)

    # set visibility to non keyable
    # TODO: make a more comprehensive visibility system through picker
    mc.setAttr(control + '.visibility', keyable = False)

    return control, hierarchyObjects


def createControlForJoint(name, joint, hierarchy=None, parent=None, constraintParent=None, shape='sphere', handle=False,
                          color='blue'):
    """Builds a control object and parents it under the given parent and hierarchy.

    :param name: name of new control object
    :type name: str

    :param joint: name of joint to control
    :type joint: str

    :param hierarchy: list of names to make a control hierarchy with
    :type hierarchy: list

    :param parent: transform to parent control to
    :type parent: str

    :param position: world space position for new object
    :type position: tuple | list

    :param shape: shape name to create
    :type shape: str

    :param color: color name or RGB value tuple/list
    :type color: str | list | tuple

    :returns: name of control
    :rtype: str
    """
    # get joint position
    position = mc.xform(joint, q=True, ws=True, rp=True)


    if hierarchy:
        if isinstance(hierarchy, basestring):
            hierarchy = [hierarchy]
        if isinstance(hierarchy, tuple):
            hierarchy = list(hierarchy)
        hierarchyNames = [name.lower() + '_' + s for s in hierarchy]
    else:
        hierarchyNames = [name.lower() + '_' + s for s in ['nul', 'ort']]

    # create control
    control, hierarchy = createControl(name=name,
                                       parent=parent,
                                       hierarchy=hierarchyNames,
                                       position=position,
                                       shape=shape,
                                       handle=handle,
                                       color=color)

    ort = hierarchy[1]
    nul = hierarchy[0]

    # constrain parent
    if constraintParent:
        if not mc.objExists(constraintParent):
            raise Exception('Constraint parent not found "%s".' % constraintParent)
        # parentPointConstraint = mc.pointConstraint(constraintParent, nul, mo=True)
        # parentOrientConstraint = mc.orientConstraint(constraintParent, nul, mo=True)
        parentConstraint = mc.parentConstraint(constraintParent, nul, mo=True)

    # orient to joint
    openrig.maya.transform.alignRotate(ort, joint)

    # constrain joint
    pointConstraint = mc.pointConstraint(control, joint)
    orientConstraint = mc.orientConstraint(control, joint)
    mc.connectAttr(control + '.scale', joint + '.scale')

    return control, hierarchy


def createControlShape(parent, shape, color):
    """Builds a control shape and parents it under the supplied transform.
    
    **Named Shapes**
    cube, sphere, cylinder, circle, square
    
    **Named Colors**
    red, blue, green, yellow, teal, pink, orange, lime, aqua, lightBlue, purple, magenta, white, black
    
    :param parent: transform to parent shape to
    :type parent: str
    
    :param shape: name of shape to create
    :type shape: str
    
    :param color: color name or RGB value list
    :type color: str | list | tuple
    
    :returns: name of shape node
    :rtype: str
    """
    # build control shape
    controlShape = parent+'Shape'
    
    if shape == 'cube':
        controlShape = mc.createNode('mesh', n=controlShape, p=parent)
        shapeBuild = mc.createNode('polyCube')
        mc.connectAttr(shapeBuild+'.output', controlShape+'.inMesh')
        mc.setAttr(controlShape+'.displaySmoothMesh', 0, e=True, l=True)
        setControlColor(controlShape, color)
        
    if shape == 'sphere':
        controlShape = mc.createNode('mesh', n=controlShape, p=parent)
        shapeBuild = mc.createNode('polyPlatonicSolid')
        mc.connectAttr(shapeBuild+'.output', controlShape+'.inMesh')
        mc.setAttr(shapeBuild+'.solidType', 2)
        mc.setAttr(controlShape+'.displaySmoothMesh ', 2, e=True, l=True)
        mc.setAttr(controlShape+'.smoothLevel', 2, e=True, l=True)
        setControlColor(controlShape, color)
        
    if shape == 'cylinder':
        controlShape = mc.createNode('mesh', n=controlShape, p=parent)
        shapeBuild = mc.createNode('polyCube')
        mc.connectAttr(shapeBuild+'.output', controlShape+'.inMesh')
        mc.setAttr(shapeBuild+'.height', 0.5)
        mc.delete(controlShape+'.f[1]', controlShape+'.f[3]')
        mc.setAttr(controlShape+'.displaySmoothMesh ', 2, e=True, l=True)
        mc.setAttr(controlShape+'.smoothLevel', 2, e=True, l=True)
        setControlColor(controlShape, color)
        
    if shape == 'circle':
        controlShape = mc.createNode('nurbsCurve', n=controlShape, p=parent)
        shapeBuild = mc.createNode('makeNurbCircle')
        mc.connectAttr(shapeBuild+'.outputCurve', controlShape+'.create')
        mc.setAttr(shapeBuild+'.normal', 0, 1, 0)
        mc.setAttr(shapeBuild+'.radius', 0.5)
    
    if shape == 'square':
        controlShape = mc.createNode('nurbsCurve', n=controlShape, p=parent)
        shapeBuild = mc.createNode('makeNurbCircle')
        mc.connectAttr(shapeBuild+'.outputCurve', controlShape+'.create')
        mc.setAttr(shapeBuild+'.normal', 0, 1, 0)
        mc.setAttr(shapeBuild+'.degree', 1)
        mc.setAttr(shapeBuild+'.sections', 4)
        mc.closeCurve(controlShape, ch=0, ps=1, rpo=True)
        mc.delete(controlShape+'.cv[4]')
        mc.xform(controlShape+'.cv[0]', ws=True, t=(0.5, 0.0, -0.5))
        mc.xform(controlShape+'.cv[1]', ws=True, t=(-0.5, 0.0, -0.5))
        mc.xform(controlShape+'.cv[2]', ws=True, t=(-0.5, 0.0, 0.5))
        mc.xform(controlShape+'.cv[3]', ws=True, t=(0.5, 0.0, 0.5))
        
    # center shape to parent
    cluster_temp = mc.cluster(controlShape)[1]
    mc.delete(mc.pointConstraint(parent, cluster_temp))
    mc.delete(controlShape, constructionHistory=True)

    # set renderable flags
    renderFlags = ['castsShadows', 'receiveShadows', 'holdOut', 'motionBlur', 'primaryVisibility', 'smoothShading',
                   'visibleInReflections', 'visibleInRefractions', 'doubleSided']
    for attribute in renderFlags:
        mc.setAttr(controlShape + '.' + attribute, 0)


    return controlShape


def addControlAttr(node):
    """Adds a control attr to supplied object.
    
    :param node: node to add attribute to
    :type node: str
    """
    mc.addAttr(node, ln='ctrl', at='bool')


def addRigControl(rigControl, parent):
    """Creates a locator shape under the supplied 'parent' node. Common control attrs can be added
    to this node. The rigControl can then be instanced to other controls, and will be visible in the
    channel box for all controls it is instanced to. If the rigControl name already exists it will
    be instanced instead of created.
    
    :param rigControl: name for rigControl
    :type rigControl: str
    
    :param parent: transform to add rigControl shape to
    :type parent: str
    
    :returns: name of the rigControl locator
    :rtype: str
    """
    # check parent
    if not mc.objExists(parent):
        raise Exception('Parent object "%s" not found in scene!' % parent)
    
    # create or instance rigControl
    if not mc.objExists(rigControl):
        rigControl = mc.createNode('locator', n=rigControl, p=parent)
        openrig.maya.attr.lockAndHideAttrs(rigControl, ['lpx', 'lpy', 'lpz', 'lsx', 'lsy', 'lsz'])
        mc.hide(rigControl)
    else:
        mc.parent(rigControl, parent, add=True, shape=True)
    
    return rigControl


def setControlColor(control, color, transparency=0.5, shaderType='lambert'):
    """Assigns a new control shader to the control if that color shader doesn't already exist.

    :param control: name of control to assign color to
    :type control: str

    :param color: shader color value
    :type color: tuple | list | str

    :param transparency: shader transparency value
    :type transparency: tuple | list | str | int | float

    :param shaderType: shader type name ('lambert')
    :type shaderType: str

    :return: name of shader
    """
    colorName = str()
    if not isinstance(color, basestring):
        rgb = openrig.shared.core.color.percent_to_rgb(color)
        if rgb:
            colorName = openrig.shared.core.color.rgb_to_name(rgb)
            if colorName:
                colorName = colorName.lower()
    name = (colorName or str(color)) + '_controlMat'
    shader = openrig.maya.shader.createShader(name=name,
                                                shaderType=shaderType,
                                                color=color,
                                                transparency=transparency,
                                                geo=control)
    return shader




#-------------------------------------------------------------------
# new stuff to talk about.
#-------------------------------------------------------------------
def create(name="control", controlType = "square", hierarchy=['nul'], position=[0,0,0],
        rotation=[0,0,0], hideAttrs=['v'], parent=None, color=openrig.shared.common.BLUE,
        transformType="transform", type='', rotateOrder='xyz', pickface=False):
    '''
    This function will create a control hierarchy based on the arguments that are passed in. 
    It will also make sure the control is tagged properly.

    :param name: Name you wish to use for the control.
    :type name: str

    :param controlType: The shape you would like to use for the control.
    :type controlType: str

    :param hierarchy: List of nodes to be created as parents of the control
    :type hierarchy: list | tuple

    :param position: Point in space where the control will be positioned in the scene
    :type position: list | tuple

    :param rotation: Rotation in space where the control will be rotated in the scene
    :type rotation: list | tuple

    :param hideAttrs: List of attributes you wish to lock and hide from the channel box.
    :type hideAttrs: list | tuple

    :param parent: Parent for the controls nul node
    :type parent: str

    :param color: Color you 
    :type color: int

    :param transformType: Type of transform for the control. (i.e "transform", "joint")
    :type transformType: str

    :param rotateOrder: Specify which rotate order you want the control to be.('xyz', 'yzx', 'zxy', 'xzy', 'yxz', 'zyx')
    :type rotateOrder: str


    '''
    curveData = openrig.maya.data.curve_data.CurveData()
    curveData.read(CONTROLPATH)
    data = curveData.getData()
    if data.has_key(controlType):
        shapeList = data[controlType]["shapes"].keys()
        for shape in shapeList:
            if shape == shapeList[0]:
                control = openrig.maya.curve.createCurveFromPoints(data[controlType]["shapes"][shape]['cvPositions'],
                    degree=data[controlType]['shapes'][shape]['degree'],name=name, transformType=transformType)
                continue
            curve = openrig.maya.curve.createCurveFromPoints(data[controlType]["shapes"][shape]['cvPositions'],
                    degree=data[controlType]['shapes'][shape]['degree'],name=name, transformType=transformType)
            curveShape = mc.listRelatives(curve, c=True, shapes=True)[0]
            mc.parent(curveShape, control, r=True, s=True)
            mc.rename(curveShape, "{}Shape".format(control))
            mc.delete(curve)
    elif controlType == "circle":
        if not hierarchy:
            control = name
        else:
            control = mc.createNode(transformType, name=name)

        curve = mc.circle(name=name+'_curve', c=(0, 0, 0), nr=(0, 1, 0), sw=360, r=1,
                          d=3, ut=0, tol=0.01, s=8, ch=False) [0]
        curveShape = mc.parent(mc.listRelatives(curve, c=True, shapes=True, type="nurbsCurve")[0], control, r=True, s=True)
        mc.rename(curveShape, control+'Shape')

        mc.delete(curve)
    else:
        control = mc.createNode(transformType, name=name)
        mc.setAttr("{0}.displayHandle".format(control), 1)

    if pickface:
        line = mc.curve(n=control + '_pickface', d=1, p=[(0, 0, 0), (0, .0001, 0)], k=[0, 1])
        line_shape = mc.listRelatives(line, s=1)[0]
        line_shape = mc.rename(line_shape, control + '_pickfaceShape')

        mc.parent(line_shape, control, add=1, s=1)[0]
        mc.delete(line)

    if transformType == "joint":
        hideAttrs.append("radius")

    for attr in hideAttrs:
        if mc.objExists(control+'.'+attr):
            mc.setAttr(control+'.'+attr, k=0, cb=0)

    # set the rotate order for the control based on what was passed in. If it's not in the list, then it
    # will stay default
    enumList = mc.attributeQuery('rotateOrder', node=control, listEnum=True)[0].split(":")

    if rotateOrder in enumList:
        mc.setAttr('{}.rotateOrder'.format(control), enumList.index(rotateOrder))

    parent = parent

    hierarchyList = []

    # If there is a hierarchy argument passed in. We will loop through and create the hiearchy.
    if hierarchy:
        for suffix in hierarchy:
            node = mc.createNode("transform", n="{0}_{1}".format(control, suffix))
            if parent:
                mc.parent(node, parent)

            parent = node
            hierarchyList.append(node)
    # parent the control to the last hierachy node created.
    if parent:
        mc.parent(control, parent)

    if position and hierarchyList:
        mc.xform(hierarchyList[0], ws=True, t=position)

    if rotation and hierarchyList:
        mc.xform(hierarchyList[0], ws=True, rotation=rotation)

    if color:
        mc.setAttr("{0}.overrideEnabled".format(control), 1)
        mc.setAttr("{0}.overrideColor".format(control), color)

    if mc.nodeType(control) == "joint":
        mc.setAttr("{}.drawStyle".format(control), 2)

    tagAsControl(control, type=type)

    return hierarchyList + [control]

def tagAsControl(ctrl, type=''):
    '''
    :param control: node to tag as a control
    :type control: str or list
    '''
    if not isinstance(ctrl, (tuple,list)):
        if not isinstance(ctrl, basestring):
            raise TypeError('{0} must be of type str, unicode, or list'.format(ctrl))
        ctrls = openrig.shared.common.toList(ctrl)
    else:
        ctrls = openrig.shared.common.toList(ctrl)

    for ctrl in ctrls:
        tagAttr = '{}.__control__'.format(ctrl)
        if not mc.objExists(tagAttr):
            mc.addAttr(ctrl, ln='__control__', at='message')
        if type:
            typeTagAttr = '__{}_control__'.format(type)
            if not mc.objExists(ctrl+'.'+typeTagAttr):
                mc.addAttr(ctrl, ln=typeTagAttr, at='message')

    return tagAttr

def untagAsControl(ctrl):
    '''
    :param control: node to tag as a control
    :type control: str or list
    '''
    if not isinstance(ctrl, (tuple,list)):
        if not isinstance(ctrl, basestring):
            raise TypeError('{0} must be of type str, unicode, or list'.format(ctrl))
        ctrls = openrig.shared.common.toList(ctrl)
    else:
        ctrls = openrig.shared.common.toList(ctrl)

    for ctrl in ctrls:
        userAttributes = mc.listAttr(ctrl, ud=True) or list()
        for tagAttr in userAttributes:
            if 'control__' in tagAttr:
                mc.deleteAttr(ctrl, at=tagAttr)


def getControls(namespace = None):
    '''
    Gets all controls connect to an asset or every control in the scene depending on user input

    :param namespace: Asset you wish to look for controls on
    :type namespace: str

    :return: List of controls
    :rtype: list
    '''
    controls = None
    if not namespace:
        controls = mc.ls('*.__control__'.format(), fl=True, o=True)
    elif namespace:
        controls = mc.ls('{}:*.__control__'.format(namespace), fl=True, o=True)

    return controls


def setPoseAttr(controls, poseAttr=0):
    '''
    This will store all of the keyable attribute values at the time this function is called. 
    It will use the pose attr argument to figure out where to store it. If the attribute 
    already exist. It will just overwrite it.

    .. example:
        setPoseAttr(openrig.maya.riglib.control.getControls())
        setPoseAttr(openrig.maya.riglib.control.getControls(),1)

    :param controls: list of controls that you want to set pose on
    :type controls: str | list

    :param poseAttr: Attribute value you want to store this pose at.
    :type poseAttr: int
    '''
    # make sure the controls are set as a list.
    controls = openrig.shared.common.toList(controls)
    skipAttrs = ("message")
    skipAttrList = ["ikfk_switch"]
    for ctrl in controls:
        # store the attribute names
        ctrlPoseAttr = "{}.poseAttr_{}".format(ctrl,poseAttr)
        poseAttrName = ctrlPoseAttr.split(".")[-1]
        ctrlAttrDict = OrderedDict()

        # go through each attribute and store it in the dictionary
        for attr in mc.listAttr(ctrl, keyable=True):
            if not mc.getAttr("{}.{}".format(ctrl,attr),type=True) in skipAttrs and not attr in skipAttrList:
                ctrlAttrDict[str(attr)] = mc.getAttr("{}.{}".format(ctrl,attr))

        # if the pose doesn't exist, then we will create it.
        if not poseAttrName in mc.listAttr(ctrl):
            mc.addAttr(ctrl, ln=poseAttrName, dt= "string")

        # set the attribute
        mc.setAttr(ctrlPoseAttr, str(ctrlAttrDict), type="string")

def toPoseAttr(controls, poseAttr=0):
    '''
    This will set the pose based on the way it was stored using setPoseAttr

    .. example:
        toPoseAttr(openrig.maya.riglib.control.getControls())
        toPoseAttr(openrig.maya.riglib.control.getControls(),1)

    :param controls: list of controls that you want to set pose on
    :type controls: str | list

    :param poseAttr: Attribute value you want to store this pose at.
    :type poseAttr: int
    '''
    # Make sure the controls are a list.
    controls = openrig.shared.common.toList(controls)
    
    # loop throught the controls and try and set the attributes back to the way they were stored.
    for ctrl in controls:
        ctrlPoseAttr = "{}.poseAttr_{}".format(ctrl,poseAttr)
        poseAttrName = ctrlPoseAttr.split(".")[-1]

        # check to see if the attribute exists.
        if not poseAttrName in mc.listAttr(ctrl):
            continue

        # if the attribute exists then we can eval it into an OrderedDict        
        ctrlAttrDict = eval(mc.getAttr(ctrlPoseAttr))

        # loop through the attributes and set them if we can.
        for attr in ctrlAttrDict:
            try:
                # set the attributes if we can.
                mc.setAttr("{}.{}".format(ctrl,attr), ctrlAttrDict[attr])
            except:
                # raise a warning for now if we can't set it. 
                #Usually this is because it's connected or locked.
                if DEBUG:
                    mc.warning("Couldn't set {}.".format(attr))

#shapes
#-----------------------
def translateShape (ctrl, translation = (0.0, 0.0, 0.0), index = 0 , world = False):
    '''
    Rotate control shape

    :param ctrl: Animation control
    :type ctrl: str

    :param translation: Translation vector
    :type translation: list

    :param index: Shape index
    :type index: int
    '''
    # Get control shape
    shape = getShape (ctrl, index)

    # Translate shape
    if world:
        mc.move (translation [0],
                translation [1],
                translation [2],
                openrig.maya.curve.getCVs (shape),
                relative = True,
                worldSpace = True)
    else:
        mc.move (translation [0],
                translation [1],
                translation [2],
                openrig.maya.curve.getCVs (shape),
                relative = True,
                objectSpace = True)

def rotateShape (ctrl, rotation = (0.0, 0.0, 0.0), index = 0):
    '''
    Rotate control shape

    :param ctrl: Animation control
    :type ctrl: str

    :param rotation: Rotation vector
    :type rotation: list

    :param index: Shape index
    :type index: int
    '''
    # Get control shape
    shape = getShapes(ctrl, index)

    # Rotate shape
    mc.rotate (rotation [0],
            rotation [1],
            rotation [2],
            openrig.maya.curve.getCVs (shape),
            relative = True,
            objectSpace = True)

def scaleShape (ctrl, scale = [1, 1, 1], index = 0):
    '''
    Rotate control shape

    :param ctrl: Animation control
    :type ctrl: str

    :param scale: Scale vector
    :type scale: list

    :param index: Shape index
    :type index: int
    '''
    # Get control shape
    shape = getShape (ctrl, index)

    # Scale shape
    mc.scale (scale [0],
            scale [1],
            scale [2],
            openrig.maya.curve.getCVs (shape),
            relative = True )

def getShape(ctrl, index = 0):
    '''
    gets shape based on index

    :param ctrl: Control you wish to get shape on
    :type ctrl: str

    :param index: Index of the shape on the control
    :type index: int
    '''
    #get shapes
    shapes = mc.listRelatives(ctrl, c=True, type="shape")

    #return shape based off of index
    if shapes:
        return shapes[index]

    return None


def displayLine(point1, point2, name = 'ctrlLine#', parent = str(), displayType=2):
    '''
    Create a display line between two points

    Example:
    ..python
        displayLine('l_uparm_sc_jnt', 'l_uparm_pv_ctrl')
        #Return: 'ctrlLine1'

        displayLine('l_uparm_sc_jnt', 'l_uparm_pv_ctrl', name = 'l_uparm_pv_displayLine')
        #Return: 'l_uparm_pv_displayLine'

    :param point1: First node to connect display line to
    :type point1: str

    :param point2: Second node to connect display line to
    :type point2: str

    :param displayType: Whether to display it as a reference or template
    :type displayType: int

    :return: Display line
    :rtype: str

    '''
    # make sure displayType is correct. If not, than instead of throwing an error. We will just
    # make sure it's set properly and let the code execute.
    if displayType not in [0,1,2]:
        mc.warning("The displayType argument must be (0,1,2). Currently it is {}. We're setting it to 2 for you since you passed in the incorrect value".format(displayType))
        displayType = 2
    #get posiitons of first and second points
    pnt1 = mc.xform(point1, q =True, ws = True, t = True)
    pnt2 = mc.xform(point2, q =True, ws = True, t = True)

    #create a pointList from point1 and point2 positions
    pointList = (pnt1,pnt2)

    #create display line from pointList
    displayLine = openrig.maya.curve.createCurveFromPoints(pointList, degree = 1, name = name)

    #cluster the two ends of the dispay line to point1 and point2
    mc.cluster( '{}.cv[0]'.format(displayLine),
            wn = [point1,point1],
            bs = True,
            name = '{}_1_{}'.format(displayLine, openrig.shared.common.CLUSTER))

    mc.cluster('{}.cv[1]'.format(displayLine),
            wn = [point2,point2],
            bs = True,
            name = '{}_2_{}'.format(displayLine, openrig.shared.common.CLUSTER))

    #override display type of displayLine to be templated
    mc.setAttr('{}.overrideEnabled'.format(displayLine), 1)
    mc.setAttr('{}.overrideDisplayType'.format(displayLine), displayType)
    mc.setAttr('{}.inheritsTransform'.format(displayLine), 0)

    if parent:
        mc.parent(displayLine, parent)

    return displayLine
