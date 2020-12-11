# this is the switch command that should be made into a script node
import maya.cmds as mc
import maya.api.OpenMaya as om2
import traceback


def getDistanceVector(distance):
    '''
    '''
    distanceValue = max(distance, key=abs)
    index = distance.index(distanceValue)
    attr = ["x", "y", "z"][index]
    value = round(distance[index], 4)
    if attr == "x":
        if value < 0:
            attr = "-x"
            vector = [-1, 0, 0]
        else:
            vector = [1, 0, 0]
    elif attr == "y":
        if value < 0:
            attr = "-y"
            vector = [0, -1, 0]
        else:
            vector = [0, 1, 0]
    elif attr == "z":
        if value < 0:
            attr = "-z"
            vector = [0, 0, -1]
        else:
            vector = [0, 0, 1]

    return (attr, vector)


def switch(paramNode, value):
    namespace = ""
    namespaceSplit = paramNode.split(":")

    if namespaceSplit > 1:
        namespace = ":".join(namespaceSplit[:-1])
        namespace = "%s:" % (namespace)

    autoClavValue = 1.0
    clavicleCtrl = None
    if mc.objExists("%s.clavicleCtrl" % paramNode):
        clavicleCtrl = "%s%s" % (namespace, mc.getAttr("%s.clavicleCtrl" % paramNode))
        clavicleValue = mc.xform(clavicleCtrl, q=True, ws=True, matrix=True)

    # To fk
    if value == 1:

        # Get transforms
        fkControls = eval(mc.getAttr(paramNode + '.fkControls'))
        ikMatchTransforms = eval(mc.getAttr(paramNode + '.ikMatchTransforms'))
        scaleNodes = eval(mc.getAttr(paramNode + '.scaleNodes'))

        aimAttr, vector = getDistanceVector(mc.getAttr("%s%s.t" % (namespace, fkControls[1]))[0])
        scaleValues = [mc.getAttr('%s%s.s%s' % (namespace, ctrl, aimAttr.strip("-"))) for ctrl in scaleNodes]
        wristGimbal = "%s%s" % (namespace, fkControls.pop(-1))

        matrixList = list()
        for node in ikMatchTransforms:
            matrixList.append(mc.xform('%s%s' % (namespace, node), q=True, ws=True, rotation=True))

        mc.setAttr("%s.pvPin" % (paramNode), 0)
        mc.setAttr("%s.twist" % (paramNode), 0)
        mc.setAttr("%s.ikfk" % (paramNode), 1)
        mc.getAttr("%s.ikfk" % (paramNode))
        mc.setAttr("%s.ikfk" % (paramNode), 1)
        mc.setAttr(wristGimbal + '.r', 0, 0, 0)

        attrList = ('stretchTop', 'stretchBottom')
        for scaleValue, attr in zip(scaleValues, attrList):
            mc.setAttr(paramNode + '.' + attr, scaleValue)

        # Auto clav requires itterative matching because I am dumb - schiller
        if clavicleCtrl:
            if mc.objExists("%s.autoClav" % clavicleCtrl):
                for i in xrange(20):
                    # limb
                    for matrix, ctrl in zip(matrixList, fkControls):
                        mc.xform('%s%s' % (namespace, ctrl), ws=True, rotation=matrix)
                    # clav
                    mc.xform('%s' % clavicleCtrl, ws=True, matrix=clavicleValue)
            else:
                for matrix, ctrl in zip(matrixList, fkControls):
                    mc.xform('%s%s' % (namespace, ctrl), ws=True, rotation=matrix)
        else:
            for matrix, ctrl in zip(matrixList, fkControls):
                mc.xform('%s%s' % (namespace, ctrl), ws=True, rotation=matrix)
    # To ik
    elif value == 0:
        # get the ik controls
        ikControls = eval(mc.getAttr(paramNode + '.ikControls'))
        fkControls = eval(mc.getAttr(paramNode + '.fkControls'))

        # Pivot ctrl
        mc.setAttr("%s%s.r" % (namespace, ikControls[3]), 0, 0, 0)
        mc.setAttr("%s%s.t" % (namespace, ikControls[3]), 0, 0, 0)

        ikMatchTransforms = eval(mc.getAttr(paramNode + '.ikMatchTransforms'))
        # get the fk transforms
        fkMatchTransforms = eval(mc.getAttr(paramNode + '.fkMatchTransforms'))
        aimAttr, vector = getDistanceVector(mc.getAttr("%s%s.t" % (namespace, fkMatchTransforms[1]))[0])
        # get the match node for the pole vector node
        matchNode = mc.getAttr(paramNode + '.pvMatch')
        # get the current distance between the joints
        currentDistance = mc.getAttr("%s%s.t%s" % (namespace, fkMatchTransforms[1], aimAttr.strip("-"))) + mc.getAttr(
            "%s%s.t%s" % (namespace, fkMatchTransforms[2], aimAttr.strip("-")))
        is_colinear = isColinear(namespace, fkMatchTransforms)
        if is_colinear:
            newPvPos = mc.xform("%s%s" % (namespace, matchNode), q=True, ws=True, t=True)
        else:
            match_fk_match_xforms = ['%s%s' % (namespace, xform) for xform in fkMatchTransforms]
            pv_vec = getPoleVectorPosition(match_fk_match_xforms, 20)
            newPvPos = (pv_vec.x, pv_vec.y, pv_vec.z)
        endJntMatrix = mc.xform("%s%s" % (namespace, fkMatchTransforms[2]), q=True, ws=True, matrix=True)
        mc.setAttr("%s.ikfk" % (paramNode), 0)
        mc.getAttr("%s.ikfk" % (paramNode))
        mc.setAttr("%s.ikfk" % (paramNode), 0)

        mc.xform("%s%s" % (namespace, ikControls[1]), ws=True, matrix=endJntMatrix)
        mc.xform("%s%s" % (namespace, ikControls[0]), ws=True, t=newPvPos)
        # Gimbal ctrl
        mc.setAttr("%s%s.r" % (namespace, ikControls[2]), 0, 0, 0)

        # Match Clav
        if clavicleCtrl:
            if mc.objExists("%s.autoClav" % clavicleCtrl):
                # mc.setAttr("%s.autoClav" % paramNode, autoClavValue)
                mc.xform(clavicleCtrl, ws=True, matrix=clavicleValue)

                # get the vector for the fk and ik middle match transforms
        fkVector = om2.MVector(*mc.xform("%s%s" % (namespace, fkControls[1]), q=True, ws=True, t=True))
        ikVector = om2.MVector(*mc.xform("%s%s" % (namespace, ikMatchTransforms[1]), q=True, ws=True, t=True))

        # get the difference between the two vectors.
        vector = fkVector - ikVector
        # if the magnitude is not within the threshold passed by the user, then we will recursively
        # go through and try to get as close as possible.
        if not vector.length() <= .001:
            recursiveMatch(paramNode, fkVector, "%s%s" % (namespace, ikMatchTransforms[1]), .001, 200, step=.001)


def recursiveMatch(paramNode, fkVector, ikMiddleJoint, threshold, attempts=5, direction=True, step=.001,
                   originalMagnitude=1):
    '''
    This will recursively go through and try to match
    the top and bottom stretch attributes to get the elbow
    to be within a threshold.

    :param paramNode: Node that holds the top/bottom attributes
    :type paramNode: str

    :param fkVector: fk original position we're trying to match
    :type fkVector: MVector

    :param ikMiddleJoint: ik joint
    :type ikMiddleJoint: str

    :param threshold: If we land within this distance, we will return
    :type threshold: float

    :param attempts: Number of time you want to try to match
    :type attempts: int
    '''
    # first check and see if we need to return
    if not mc.objExists(paramNode) or attempts == 0:
        return

    # get the new ikVector position.
    ikVector = om2.MVector(*mc.xform(ikMiddleJoint, q=True, ws=True, t=True))

    # get the difference between the two vector's to be able to get the magnitude.
    vector = fkVector - ikVector
    magnitude = vector.length()

    # if the magnitude is within a threshold, we will return
    if magnitude <= threshold:
        return

    # if the magnitude is larger then we will subtract by .001
    # NOTE:: We may want a user when building be able to pass this number in.
    if direction:
        mc.setAttr("%s.stretchTop" % paramNode, mc.getAttr("%s.stretchTop" % paramNode) + step)
        mc.setAttr("%s.stretchBottom" % paramNode, mc.getAttr("%s.stretchBottom" % paramNode) + step)
    else:
        mc.setAttr("%s.stretchTop" % paramNode, mc.getAttr("%s.stretchTop" % paramNode) - step)
        mc.setAttr("%s.stretchBottom" % paramNode, mc.getAttr("%s.stretchBottom" % paramNode) - step)

    # # get the new ikVector position.
    ikVector = om2.MVector(*mc.xform(ikMiddleJoint, q=True, ws=True, t=True))

    # get the difference between the two vector's to be able to get the magnitude.
    vector = fkVector - ikVector
    newMagnitude = vector.length()
    if newMagnitude > magnitude:
        direction = not direction
    if originalMagnitude == newMagnitude:
        step /= 2
    # return the recursive function that we're currently in.
    return recursiveMatch(paramNode, fkVector, ikMiddleJoint, threshold, attempts=attempts - 1, direction=direction,
                          step=step, originalMagnitude=magnitude)


def armSwitch(paramNode, value):
    '''
    '''
    mc.undoInfo(openChunk=1)
    try:
        print 'armSwitch(paramNode="%s", value=%s)' % (paramNode, value)
        switch(paramNode, value)
    except:
        traceback.print_exc()
    mc.undoInfo(closeChunk=1)


def legSwitch(paramNode, value):
    '''
    '''
    mc.undoInfo(openChunk=1)
    try:
        namespace = ""
        namespaceSplit = paramNode.split(":")

        if len(namespaceSplit) > 1:
            namespace = ":".join(namespaceSplit[:-1])
            namespace = "%s:" % (namespace)

        print 'legSwitch(paramNode="%s", value=%s)' % (paramNode, value)
        if value == 1:
            fkControl = mc.getAttr("%s.footFkControl" % (paramNode))
            fkControlPos = mc.xform("%s%s" % (namespace, fkControl), q=True, ws=True, matrix=True)
            print fkControl
            switch(paramNode, value)
            mc.xform("%s%s" % (namespace, fkControl), ws=True, matrix=fkControlPos)
        elif value == 0:
            footIkControls = eval(mc.getAttr(paramNode + '.footIkControls'))
            print footIkControls
            for ctrl in footIkControls:
                attrs = mc.listAttr("%s%s" % (namespace, ctrl), ud=False, keyable=True)
                for attr in attrs:
                    try:
                        mc.setAttr("%s%s.%s" % (namespace, ctrl, attr), 0.0)
                    except:
                        pass

            switch(paramNode, value)
    except:
        traceback.print_exc()
    mc.undoInfo(closeChunk=1)


def rig_reset_foot(param):
    # Get namespace
    namespace = ""
    namespaceSplit = param.split(":")

    if namespaceSplit > 1:
        namespace = ":".join(namespaceSplit[:-1])
        namespace = "%s:" % (namespace)

    # Get data from param
    ik_foot_controls = eval(mc.getAttr(param + '.footIkControls'))
    ik_bank, ik_heel, ik_toe, ik_ball, toeBend = ik_foot_controls

    ik_controls = eval(mc.getAttr(param + '.ikControls'))
    ik_pv, ik_ankle, ik_ankle_gimbal, ik_mpivot = ik_controls

    fk_ball = eval(mc.getAttr(param + '.footFkControl'))
    ik_handle = mc.listConnections("%s.twist" % (param), scn=True)[0]

    # Get matrices
    fk_ball_matrix = mc.xform("%s%s" % (namespace, fk_ball), q=True, ws=True, matrix=True)
    ik_ankle_matrix = mc.xform(ik_handle, q=True, ws=True, matrix=True)

    # zero ik controls
    mc.setAttr("%s%s%s" % (namespace, ik_heel, '.r'), 0, 0, 0)
    mc.setAttr("%s%s%s" % (namespace, ik_ball, '.r'), 0, 0, 0)
    mc.setAttr("%s%s%s" % (namespace, ik_toe, '.r'), 0, 0, 0)
    mc.setAttr("%s%s%s" % (namespace, ik_mpivot, '.r'), 0, 0, 0)
    mc.setAttr("%s%s%s" % (namespace, ik_bank, '.tx'), 0)
    mc.setAttr("%s%s%s" % (namespace, ik_bank, '.tz'), 0)
    mc.setAttr("%s%s%s" % (namespace, ik_ankle_gimbal, '.r'), 0, 0, 0)
    mc.setAttr("%s%s%s" % (namespace, ik_ankle_gimbal, '.t'), 0, 0, 0)

    # Set matrices
    mc.xform("%s%s" % (namespace, ik_ankle), ws=True, matrix=ik_ankle_matrix)
    mc.xform("%s%s" % (namespace, fk_ball), ws=True, matrix=fk_ball_matrix)


def getPoleVectorPosition(match_list, magnitude=10, attempts=20):
    '''
    This will return a position for the polevector
    '''
    print match_list
    if len(match_list) != 3:
        raise RuntimeError("{0} must be a lenght of three and a list.".format(match_list))

    # getting postions to use for the vectors.
    match1Pos = mc.xform('%s' % match_list[0], q=True, ws=True, t=True)
    match2Pos = mc.xform('%s' % match_list[1], q=True, ws=True, t=True)
    match3Pos = mc.xform('%s' % match_list[2], q=True, ws=True, t=True)

    # create vector from world space positions
    vector1 = om2.MVector(*match1Pos)
    vector2 = om2.MVector(*match2Pos)
    vector3 = om2.MVector(*match3Pos)

    # getting the final polevector position.
    mid_vec = (vector1 + vector3) / 2
    mid_diff_vec = vector2 - mid_vec
    mid_diff_vec = match_magnitude(mid_diff_vec, magnitude + mid_diff_vec.length(), attempts=attempts)
    pv_vec = mid_diff_vec + mid_vec
    return pv_vec


def isColinear(namespace, match_list, threshold=.008):
    '''
    Will return true if the
    :param pv_vec:
    :return:
    '''
    if len(match_list) != 3:
        raise RuntimeError("{0} must be a lenght of three and a list.".format(match_list))
    mid_vec = om2.MVector(*mc.xform('%s:%s' % (namespace, match_list[1]), q=True, ws=True, t=True))
    first_node_vec = om2.MVector(*mc.xform('%s:%s' % (namespace, match_list[0]), q=True, ws=True, t=True))
    last_node_vec = om2.MVector(*mc.xform('%s:%s' % (namespace, match_list[-1]), q=True, ws=True, t=True))
    pv_diff_vec = first_node_vec - mid_vec
    last_diff_vec = first_node_vec - last_node_vec
    if pv_diff_vec.isParallel(last_diff_vec, threshold):
        return True
    return False


def match_magnitude(vector, magnitude, attempts=20):
    '''
    :param magnitude:
    :param current_mag:
    :return:
    '''
    if not vector.length() >= magnitude and attempts > 0:
        vector = vector * 2
        return match_magnitude(vector, magnitude, attempts - 1)
    return vector