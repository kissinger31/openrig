"""
Shader function library

"""
import maya.cmds as mc
import maya.api.OpenMaya as om2
from openrig.maya import attr
import openrig.maya.naming
import openrig.maya.shape
import openrig.shared.color

SGINPUTS = ['surfaceShader', 'volumeShader', 'displcementShader']


def getShaders():
    """Return all shading groups within the current scene

    :returns: list of shading engines in scene
    :rtype: list
    """
    sgs = mc.ls(type='shadingEngine')
    sgs.remove('initialParticleSE')
    sgs.remove('initialShadingGroup')

    return sgs


def getConnectedShaders(obj):
    """Return all shading groups connected to the given object.
    
    :param obj: name of any mesh or nurbsSurface
    :type obj: str
    
    :returns: list of shader groups
    :rtype:
    """
    # get shapes
    shapes = openrig.maya.shape.getShapes(obj)
    
    # get shading groups
    shadingGroups = set()
    for shape in shapes:
        selList = om2.MSelectionList()
        selList.add(shape)
        shapeNode = selList.getDependNode(0)
        apiType = shapeNode.apiType()
        shapeFn = None
        if apiType == om2.MFn.kMesh:
            shapeFn = om2.MFnMesh(shapeNode)
        elif apiType == om2.MFn.kNurbsSurface:
            shapeFn = om2.MFnNurbsSurface(shapeNode)
        else:
            mc.warning('Shape type "%s" not supported' % mc.nodeType(shape))
            continue
        if shapeFn:
            for shader in shapeFn.getConnectedShaders(0)[0]:
                shaderFn = om2.MFnDependencyNode(shader)
                shadingGroups.add(shaderFn.name())
    
    return list(shadingGroups)


def getConnectedShadersDict(mesh):
    """Return all shaders currently connected to any faces on the mesh

    :param mesh: input mesh to check shaders
    :type mesh: str

    :returns: dictionary of mesh names and shader dictionary
    :rtype: dict
    """
    # get mesh as api object
    sel_list = om2.MSelectionList()
    sel_list.add(mesh)
    node_obj = sel_list.getDagPath(0)

    mesh_fn = om2.MFnMesh(node_obj)

    # get shaders
    connectedSGs = mesh_fn.getConnectedShaders(0)

    # add to shells dictionary
    shaderDict = dict()
    for s in set(connectedSGs[1]):
        shaderDict[s] = set([i for i, face in enumerate(connectedSGs[1]) if face == s])

    # rebuild with proper naming
    connected = dict()
    for key in shaderDict:
        dfn = om2.MFnDependencyNode(connectedSGs[0][key])
        connected[dfn.name()] = shaderDict[key]

    meshShaders = {mesh: connected}

    return meshShaders


def getMatNetwork(mat):
    """Returns a single material network and all inbound connections as a YAML dictionary

    :param mat: material to write
    :type mat: str

    :return: YAML compliant dictionary
    :rtype: dict
    """
    # dict to store info
    network = {mat: {}}

    # recursively get network
    def getNetwork(mat):
        """ Recursively add network nodes"""
        # get general node type
        nodeType = mc.nodeType(mat)

        # get specific type
        asType = mc.getClassification(nodeType)[0]
        if 'pattern' in asType or 'texture' in asType:
            asType = 'asTexture'
        elif 'utility' in asType:
            asType = 'asUtility'
        elif 'light' in asType:
            asType = 'asLight'
        else:
            asType = 'asShader'

        # get all node attributes and values
        attrs = {}
        for a in mc.listAttr(mat, hasData=True):
            try:
                attrs[a] = attr.getPlugValue('{0}.{1}'.format(mat, a))
            except:
                mc.warning('{0}.{1} not retrieved'.format(mat, a))

        # get connections to the node
        connections = {}
        connectors = []

        connectlist = mc.listConnections(mat, connections=True, destination=False, plugs=True)
        if not connectlist == None:
            for i in range(0, len(connectlist), 2):
                attrib = connectlist[i].split('.')[1]
                connectors.append(connectlist[i + 1].split('.')[0])
                connections[attrib] = connectlist[i + 1]

        # list of nodes that are connected for recursive IO
        connectors = list(set(connectors))

        # append to dictionary of node attributes
        network[mat] = {'asType': asType, 'attr': attrs,
                        'connection': connections, 'type': nodeType}

        # recursive if there are connected nodes
        if connectors:
            for node in connectors:
                getNetwork(node)

    getNetwork(mat)

    return network


def getMatNetworks():
    """Return a dict of all material networks within the current file

    :returns: all material networks
    :rtype: dict
    """
    networks = {}

    # first get all shading engines
    sgs = getShaders()
    mats = []

    # get all materials connect
    for sg in sgs:
        # get shading group connections
        conn = getShaderBinding(sg)

        for value in conn.itervalues():
            for key, value in value.iteritems():
                if key in SGINPUTS:
                    mats.append(value.split('.')[0])

    # get and merge all networks in to single dict
    for mat in mats:
        networks.update(getMatNetwork(mat))

    return networks


def getShaderBinding(shader):
    """Get the connections on either side of the shading group

    :param shader: Input shader to return connections on
    :type shader: str

    :returns: dict with shader connections
    :rtype: dict
    """
    binding = {shader: {}}

    # get connections
    connectlist = mc.listConnections(shader, connections=True, destination=False, plugs=True)
    
    # build dict
    if not connectlist == None:
        for i in range(0, len(connectlist), 2):
            plug = connectlist[i].split('.')[1]
            binding[shader][plug] = connectlist[i + 1]

    return binding


def getShaderBindings():
    """Return a dict of all shading engines with material and geometry connections

    :returns: material and geo connections to shader
    :rtype: dict
    """
    shaders = {}

    # get all sg
    sgs = getShaders()

    for sg in sgs:
        shaders.update(getShaderBinding(sg))

    return shaders


def createMatNetwork(networks, force=False):
    """Create all material networks from an input dict

    :returns: None
    """
    # # temp for testing
    # networks = getMatNetworks()
    # # comparative name dict
    created_mats = {}

    # build each node checking for each as a node failure will mean connection failures
    def createMatNode(mat_name, mat_properties):
        """Create a material type node
        """
        # set bool for asType
        shader, tex, util, light = False, False, False, False

        if mat_properties['asType'] == 'asLight':
            light = True
        if mat_properties['asType'] == 'asUtility':
            util = True
        if mat_properties['asType'] == 'asTexture':
            tex = True
        else:
            shader = True

        # create node
        mat_node = mc.shadingNode(mat_properties['type'], name=mat_name,
                                  asShader=shader, asTexture=tex, asUtility=util, asLight=light)

        # set attributes
        for key, value in mat_properties['attr'].iteritems():
            try:
                attr.setPlugValue('{0}.{1}'.format(mat_node, key), value)
            except:
                mc.warning('{0}.{1} was not set.'.format(mat_node, key))

        return mat_node

    # run create
    for key, value in networks.iteritems():
        # create node with attributes
        try:
            created_mats[key] = createMatNode(key, value)
        except:
            if not force:
                raise Exception('Node {0} could not be created, stopping'.format(key))
            else:
                continue

    # connect nodes using internal connection func
    def createMatConnection(mat_name, mat_connections, created_mats):
        """Make a connection between the given node and it's specified connections
        """
        # make connections while resolving connect to names
        connect = []
        for key, value in mat_connections.iteritems():
            key = '{0}.{1}'.format(mat_name, key)
            value = '{0}.{1}'.format(created_mats[value.split('.')[0]], value.split('.')[1])
            connect.append(mc.connectAttr(value, key, force=True))
        return connect

    # run connect
    for key, value in networks.iteritems():
        try:
            connect = createMatConnection(created_mats[key], value['connection'], created_mats)
        except:
            if not force:
                raise Exception('Connections from {0} could not be made.'.format(key))

    return True


def createShaderBinding(bindings):
    """Create shading group nodes and make connections based on the the input dictionary

    :param bindings: dictionary holding the nodes to be created and their material and 
                    object connections
    :type bindings dict

    :returns: success
    :rtype: bool
    """
    # temp for testing
    bindings = getShaderBindings()
    print bindings

    failure = False
    # create nodes
    for key, value in bindings.iteritems():
        node = mc.shadingNode('shadingEngine', name=key, asShader=True)

        # connect node to materials and objects if they exist
        for key in value.iterkeys():
            try:
                connect = mc.connectAttr(value[key], '{0}.{1}'.format(node, key))
            except:
                mc.warning('{0} has a current connection, please inspect.'.format(value[key]))
                failure = True

    if failure:
        return False
    return True


def createShader(name=None, shaderType='lambert', color=None, transparency=None, geo=None):
    """Create a simple shader with a given color and apply it to given geo.
    
    :param name: name of new shader (None == shaderType)
    :type name: str | None
    
    :param shaderType: type of shader node ('lambert')
    :type shaderType: str
    
    :param color: color name or rgb triplet in 0.0-1.0 color space (None)
    :type color: str | tuple | list | None
    
    :param transparency: transparency value for new shader (None)
    :type transparency: tuple | list | float
    
    :param geo: geometry to apply shader to (None)
    :type geo: str | list | None
    
    :returns: shader name
    :rtype: str
    """
    # get name
    name = name if name is not None else shaderType
    
    # get color
    if isinstance(color, basestring):
        try:
            color = openrig.shared.core.color.format_color_name(color)
            color = openrig.shared.core.color.name_to_rgb(color, True)
        except ValueError:
            color = None
    elif isinstance(color, (tuple, list)):
        try:
            color = openrig.shared.core.color.format_color_value(color)
        except ValueError:
            color = None
    
    # get geo
    geo = mc.ls(geo)
    
    # create shader
    shader = name
    if not mc.objExists(name):
        shader = mc.shadingNode(shaderType,
                                name=name,
                                asShader=True,
                                asTexture=False,
                                asUtility=False,
                                asLight=False)
        
    # set color
    if color:
        mc.setAttr(shader + '.color', color[0], color[1], color[2])
    
    # set transparency
    if isinstance(transparency, (int, float)):
        transparency = [transparency] * 3
        
    if transparency:
        mc.setAttr(shader + '.transparency', transparency[0], transparency[1], transparency[2])
    
    # assign to geo
    if geo:
        shadingGroupName = openrig.maya.naming.getUniqueName(shader + 'SG')
        shadingGroupName = mc.sets(r=True, nss=True, empty=True, name=shadingGroupName)
        mc.connectAttr(shader + '.outColor', shadingGroupName + '.surfaceShader')
        mc.sets(geo, e=True, fe=shadingGroupName)
        
    return shader
