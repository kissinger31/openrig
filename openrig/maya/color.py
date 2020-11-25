"""Color functions"""
import maya.cmds as mc
import openrig.shared.color


def setOverrideColor(objects, color):
    """Sets drawing override color of object to the provided color values.

    :param objects: list of transforms and/or shapes names
    :type objects: list | str

    :param color: color value or name
    :type color: tuple | list | string
    """
    # cast as list
    if not isinstance(objects, list):
        objects = [objects]

    # get color
    # if openrig.shared.core.color.format_color_value(color):
    #     color = openrig.shared.core.color.name_to_rgb(color, percent=True)
    color = openrig.shared.core.color.format_color_value(color)


    # color objects
    for obj in objects:
        mc.setAttr(obj + '.overrideEnabled', 1)
        mc.setAttr(obj + '.overrideRGBColors', 1)
        mc.setAttr(obj + '.overrideColorRGB', color[0], color[1], color[2])


def setOutlinerColor(objects, color):
    """Sets  outliner color of object to the provided color values.

    :param objects: list of transforms and/or shapes names
    :type objects: list | str

    :param color: color value or name
    :type color: tuple | list | string
    """
    # cast as list
    if not isinstance(objects, list):
        objects = [objects]

    # get color
    # if openrig.shared.core.color.format_color_value(color):
    #     color = openrig.shared.core.color.name_to_rgb(color, percent=True)
    color = openrig.shared.core.color.format_color_value(color)

    # color objects
    for obj in objects:
        mc.setAttr(obj + '.useOutlinerColor', 1)
        mc.setAttr(obj + '.outlinerColor', color[0], color[1], color[2])



def setPolyColor(objects, color, reset=False, color_set=None):
    """Sets  vertex color of components to the provided color values.

    :param objects: list of poly components
    :type objects: list | str

    :param color: color value or name
    :type color: tuple | list | string
    """
    # cast as list
    if not isinstance(objects, list):
        objects = [objects]

    # get color
    # if openrig.shared.core.color.format_color_value(color):
    #     color = openrig.shared.core.color.name_to_rgb(color, percent=True)
    color = openrig.shared.core.color.format_color_value(color)

    # color objects
    
    
 


    for obj in objects:
        if '.' in obj:
            mesh = obj.split('.')[0]
        else:
            mesh = obj

        color_sets = mc.polyColorSet(mesh, query=True, allColorSets=True )
        
        if color_set is not None:
            orig_set = mc.polyColorSet(mesh, query=True, currentColorSet=True )[0]
            if color_set not in color_sets:
                mc.polyColorSet(mesh, create=True, colorSet=color_set)
            mc.polyColorSet(mesh, currentColorSet=True, colorSet=color_set)

        if reset:
            # if there are no sets to operate on, we get a command error
            if color_sets:
                mc.polyColorPerVertex(obj, rem=True)
        else:    
            mc.setAttr(mesh + '.displayColors', 1)    
            mc.polyOptions(mesh, cm='diffuse')
            mc.polyColorPerVertex(obj, rgb=color)

        if color_set is not None:
            mc.polyColorSet(mesh, currentColorSet=True, colorSet = orig_set)
