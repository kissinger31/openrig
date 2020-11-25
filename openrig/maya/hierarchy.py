"""Hierarchy functions"""
import maya.cmds as mc
from openrig.maya import naming


def create(names, parent=None, children=None):
    """Creates a simple hierarchy from a list of names.  Provide an optional parent to place the new
    hierarchy under.  Provide an optional list of children to parent them under the final object in
    the new hierarchy.

    :param names: list of names to create objects for
    :type names: list

    :param parent: optional parent for new hierarchy (default None)
    :type parent: str | None

    :param children: optional children to parent under the final hierarchy object (default None)
    :type children: str | list | None

    :returns: a list of the new hierarchy nodes
    :rtype: list
    """
    # create objects
    objects = list()
    for i in range(len(names)):
        # create
        names[i] = naming.getUniqueName(names[i])
        obj = mc.createNode('transform', n=names[i])

        # parent
        parent = names[i-1] if i > 0 else parent
        if parent:
            obj = mc.parent(obj, parent)[0]

        objects.append(obj)

    # parent children
    if children:
        mc.parent(children, objects[-1])

    return objects


def reorderSorted(parent, reverse=False):
    """Reorder children of given parent object alphabetically.

    :param parent: name of object with children objects to sort
    :type parent: str

    :param reverse: whether to reverse the sort order (False)
    :type reverse: bool
    """
    children = sorted(mc.listRelatives(parent), reverse=reverse)
    if len(children) > 1:
        for child in children:
            mc.reorder(child, b=True)


def reorderTo(obj, neighbor, after=True):
    """Reorder the given object before or after the given neighbor. The default behavior places the
    given object after the neighbor.
    
    :param obj: name of the object to reorder
    :type obj: str
    
    :param neighbor: name of sibling object
    :type neighbor: str
    
    :param after: whether to place the object after the neighbor (True).
    :type after: bool
    """
    obj = naming.getLongName(obj)
    siblings = getSiblings(obj, includeObj=True)
    neighbor = naming.getLongName(neighbor)
    if not neighbor or not neighbor in siblings:
        raise Exception('Neighbor not found.')

    if len(siblings) > 1:
        index = siblings.index(obj)
        value = siblings.index(neighbor) - index + 1
        mc.reorder(obj, r=value)

        if not after and not index == 0:
            mc.reorder(obj, r=-1)


def getNeighbors(obj):
    """Returns adjacent siblings for the given object.  If no sibling is found before or after None is
    returned.  If the object has no siblings None is returned.

    :param obj: name of DAG object
    :type obj: str

    :returns: a list of neighbors
    :rtype: list
    """
    obj = naming.getLongName(obj)
    siblings = getSiblings(obj, includeObj=True)
    if not siblings or len(siblings) < 2:
        return [None, None]

    index = siblings.index(obj)
    if index == 0:
        return [None, siblings[1]]
    elif index+1 == len(siblings):
        return [siblings[index-1], None]
    else:
        return [siblings[index-1], siblings[index+1]]


def getSiblings(obj, includeObj=False):
    """Returns a list of siblings of the given object.  If includeObj is set True the original object
    will be returned in the list of siblings.  If no siblings are found the list will be empty.

    :param obj: object to find siblings for
    :type obj: str

    :param includeObj: whether to include the given object in the return list (default False)
    :type includeObj: bool

    :returns: a list of siblings
    :rtype: list
    """
    obj = naming.getLongName(obj)
    parent = mc.listRelatives(obj, p=True, f=True)
    if parent:
        siblings = mc.listRelatives(parent[0], f=True)
    else:
        siblings = mc.ls(assemblies=True, l=True)
    
    if not includeObj:
        siblings.remove(obj)
    
    return siblings


def getTransformGraph(objects):
    """Returns a dictionary "graph" of the provided objects.  Properties with not value are returned as
    None.  For example if the object has no parent that 'parent' key will have a vaule of None.

    Each entry in the dictionary contains a dictionary of the following properties:
    {id: {
        name: '',
        type: '',
        parent: '',
        children: [],
        neighbors: [],
        translate: [],
        rotate: [],
        scale: []
        }
     ...
    }

    :param objects: list of transforms to graph
    :type objects: list | str

    :returns: a dictionary of object entries with specified properties
    :rtype: dict
    """
    # get objects as list
    if not isinstance(objects, list): objects = [objects]

    # build graph dictionary
    graph = dict()
    for i in range(len(objects)):
        obj = naming.getLongName(objects[i])

        # get values
        name = obj.split('|')[-1]
        objType = 'mesh' if mc.listRelatives(obj, s=True, type='mesh') else 'group'
        parent = mc.listRelatives(obj, p=True, f=True)
        parent = naming.getShortName(parent[0]) if parent else None
        children = [naming.getShortName(c) for c in mc.listRelatives(obj, f=True) or []]
        neighbors = [None, None]
        for neighbor in getNeighbors(obj):
            if neighbor:
                neighbors.append(naming.getShortName(neighbor))
            else:
                neighbors.append(neighbor)

        transform = True if mc.nodeType(obj) == 'transform' else False
        translate = mc.getAttr(obj+'.t') if transform else None
        rotate = mc.getAttr(obj+'.r') if transform else None
        scale = mc.getAttr(obj+'.s') if transform else None

        # set values
        graph[i] = {
            'name': name,
            'type': objType,
            'parent': parent,
            'children': children,
            'neighbors': neighbors,
            'translate': translate,
            'rotate': rotate,
            'scale': scale
            }

    return graph