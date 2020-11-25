"""Naming functions"""
import re
import maya.cmds as mc


def getLongName(obj):
    """Returns the full path for the given object.

    :param obj: object partial path
    :type obj: str

    :returns: long name
    :rtype: str | None
    """
    if not mc.objExists(obj):
        mc.warning('Object "%s" does not exist.' % obj)
        return
    return str(mc.ls(obj, l=True)[0])


def getShortName(obj):
    """Returns the name for the given object with no path even if the name is
    not unique.

    :param obj: object partial path
    :type obj: str

    :returns: short name
    :rtype: str | None
    """
    if not mc.objExists(obj):
        mc.warning('Object "%s" does not exist.' % obj)
        return
    return str(mc.ls(obj, l=True)[0].split('|')[-1])


def isUniqueName(name):
    """Test whether the name is unique in the scene.
    
    :param name: name to test
    :type name: str
    
    :returns: whether the name is unique or not
    :rtype: bool
    """
    if not mc.objExists(name):
        mc.warning('Object "%s" does not exist.' % name)
        return
    return False if len(mc.ls(name)) > 1 else True


def getUniqueName(name):
    """Returns a unique name with the next number increment if necessary. Tests
    desired name against existing names in scene.
    
    :param name: name to test
    :type name: str
    
    :returns: unique name
    :rtype: str
    """
    # return name if it is the only one in the scene
    if isUniqueName(name):
        return name

    # get base name
    baseName = name.rstrip('0123456789')

    # find similarly named objects
    # objects with same base name and trailing digits
    similar = list()
    for obj in mc.ls(baseName + '*'):
        bn = getShortName(obj).rstrip('0123456789')
        if bn == baseName:
            sn = getShortName(obj)
            if sn not in similar:
                similar.append(sn)

    # get unique name
    if name in similar:
        # append next number to name
        numbers = list()
        for n in similar:
            match = re.match('.*?([0-9]+)$', n)
            if match:
                numbers.append(match.group(1))
        if numbers:
            name = baseName + str(int(sorted(numbers)[-1]) + 1)
        else:
            name = baseName + '1'
    
    return name
