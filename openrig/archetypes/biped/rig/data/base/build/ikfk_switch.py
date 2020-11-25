# this is the switch command that should be made into a script node
import maya.cmds as mc
import maya.api.OpenMaya as om
import traceback
																																																			
def getDistanceVector(distance):
        '''
        '''
        distanceValue = max(distance, key=abs)
        index = distance.index(distanceValue)
        attr = ["x","y","z"][index]
        value = round(distance[index], 4)
        if attr == "x":
            if value < 0:
                attr = "-x"
                vector = [-1,0,0]
            else:
                vector = [1,0,0]
        elif attr == "y":
            if value < 0:
                attr = "-y"
                vector = [0,-1,0]
            else:
                vector = [0,1,0]
        elif attr == "z":
            if value < 0:
                attr = "-z"
                vector = [0,0,-1]
            else:
                vector = [0,0,1]

        return (attr, vector)

def switch(paramNode, value):
    
    namespace=""
    namespaceSplit = paramNode.split(":")

    if namespaceSplit > 1:
        namespace = ":".join(namespaceSplit[:-1]) 
        namespace = "%s:" % (namespace)

    autoClavValue = 1.0
    clavicleCtrl = None
    if mc.objExists("%s.autoClav" % paramNode):
        clavicleCtrl = "%s%s" % (namespace, mc.getAttr("%s.clavicleCtrl" % paramNode))
        clavicleValue = mc.xform(clavicleCtrl, q=True, ws=True, matrix=True)

    # To fk
    if value == 1:

        # Get transforms
        fkControls = eval(mc.getAttr(paramNode + '.fkControls'))
        ikMatchTransforms = eval(mc.getAttr(paramNode + '.ikMatchTransforms'))
        
        aimAttr, vector= getDistanceVector(mc.getAttr("%s%s.t" % (namespace,fkControls[1]))[0])
        scaleValues = [mc.getAttr('%s%s.s%s' % (namespace,ctrl,aimAttr.strip("-"))) for ctrl in (ikMatchTransforms[0],ikMatchTransforms[1])]
        wristGimbal = "%s%s" % (namespace,fkControls.pop(-1))
        rotationList = list()
        
        # Query transforms
        for ctrl in ikMatchTransforms:
            rotationList.append(mc.xform("%s%s" % (namespace, ctrl), q=True, ws=True, rotation=True))

        mc.setAttr("%s.pvPin" % (paramNode), 0)
        mc.setAttr("%s.twist" % (paramNode), 0)
        mc.setAttr("%s.ikfk" % (paramNode), 1)
        mc.getAttr("%s.ikfk" % (paramNode))
        mc.setAttr("%s.ikfk" % (paramNode), 1)
        mc.setAttr(wristGimbal + '.r',0, 0, 0)
        
        # Match limb
        for rotation, ctrl in zip(rotationList,fkControls):
            mc.xform("%s%s" % (namespace, ctrl), ws=True, rotation=rotation)
    
        attrList = ('stretchTop', 'stretchBottom')
        for scaleValue, attr in zip(scaleValues, attrList):
            mc.setAttr(paramNode + '.' + attr, scaleValue)

        # Auto clav requires itterative matching because I am dumb - schiller
        if mc.objExists("%s.autoClav" % paramNode):
            for i in xrange(${recursive_attempts}):
                # limb
                for rotation, ctrl in zip(rotationList,fkControls):
                    mc.xform("%s%s" % (namespace, ctrl), ws=True, rotation=rotation) 
                # clav    
                mc.xform(clavicleCtrl, ws=True, matrix=clavicleValue)        
    
    # To ik
    elif value == 0:

        # get the ik controls
        ikControls = eval(mc.getAttr(paramNode + '.ikControls'))
        fkControls = eval(mc.getAttr(paramNode + '.fkControls'))

        # Pivot ctrl
        mc.setAttr("%s%s.r" % (namespace, ikControls[3]), 0,0,0)
        mc.setAttr("%s%s.t" % (namespace, ikControls[3]), 0,0,0)

        ikMatchTransforms = eval(mc.getAttr(paramNode + '.ikMatchTransforms'))
        # get the fk transforms
        fkMatchTransforms = eval(mc.getAttr(paramNode + '.fkMatchTransforms'))
        aimAttr, vector= getDistanceVector(mc.getAttr("%s%s.t" % (namespace,fkMatchTransforms[1]))[0])
        # get the match node for the pole vector node
        matchNode = mc.getAttr(paramNode + '.pvMatch')
        # get the current distance between the joints
        currentDistance = mc.getAttr("%s%s.t%s" % (namespace, fkMatchTransforms[1], aimAttr.strip("-"))) + mc.getAttr("%s%s.t%s" % (namespace, fkMatchTransforms[2], aimAttr.strip("-")))
            
        newPvPos = mc.xform("%s%s" % (namespace, matchNode), q=True, ws=True, t=True)
        endJntMatrix = mc.xform("%s%s" % (namespace,fkMatchTransforms[2]), q=True, ws=True, matrix=True)
        mc.setAttr("%s.ikfk" % (paramNode), 0)
        mc.getAttr("%s.ikfk" % (paramNode))
        mc.setAttr("%s.ikfk" % (paramNode), 0)
        
        mc.xform("%s%s" % (namespace, ikControls[1]), ws=True, matrix=endJntMatrix)
        mc.xform("%s%s" % (namespace, ikControls[0]), ws=True, t=newPvPos)
        # Gimbal ctrl
        mc.setAttr("%s%s.r" % (namespace, ikControls[2]), 0,0,0)

        # Match Clav 
        if mc.objExists("%s.autoClav" % paramNode):
            #mc.setAttr("%s.autoClav" % paramNode, autoClavValue)
            if clavicleCtrl:
                mc.xform(clavicleCtrl, ws=True, matrix=clavicleValue)     
        
        # get the vector for the fk and ik middle match transforms
        fkVector = om.MVector(*mc.xform("%s%s" % (namespace,fkControls[1]), q=True, ws=True, t=True))
        ikVector = om.MVector(*mc.xform("%s%s" % (namespace,ikMatchTransforms[1]), q=True, ws=True, t=True))

        # get the difference between the two vectors.
        vector = fkVector - ikVector

        # if the magnitude is not within the threshold passed by the user, then we will recursively
        # go through and try to get as close as possible.
        if not vector.length() <= .1:
            recursiveMatch(paramNode, fkVector, "%s%s" % (namespace,ikMatchTransforms[1]), .1, 20)

def recursiveMatch(paramNode, fkVector, ikMiddleJoint, threshold, attempts=5):
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
    ikVector = om.MVector(*mc.xform(ikMiddleJoint, q=True, ws=True, t=True))


    # get the difference between the two vector's to be able to get the magnitude.
    vector = fkVector - ikVector
    magnitude = vector.length()

    # if the magnitude is within a threshold, we will return
    if magnitude <= threshold:
        return

    # if the magnitude is larger then we will subtract by .001
    # NOTE:: We may want a user when building be able to pass this number in.
    if magnitude > threshold:
        mc.setAttr("%s.stretchTop" % paramNode, mc.getAttr("%s.stretchTop" % paramNode) - .001)
        mc.setAttr("%s.stretchBottom" % paramNode, mc.getAttr("%s.stretchBottom" % paramNode) - .001)
    else:
        mc.setAttr("%s.stretchTop" % paramNode, mc.getAttr("%s.stretchTop" % paramNode) + .001)
        mc.setAttr("%s.stretchBottom" % paramNode, mc.getAttr("%s.stretchBottom" % paramNode) + .001)

    # return the recursive function that we're currently in.
    return recursiveMatch(paramNode, fkVector, ikMiddleJoint, threshold, attempts=attempts-1)


def armSwitch():
    '''
    '''
    mc.undoInfo(openChunk=1)
    try:
        paramNode = mc.ls(sl=True)[0]
        connections = mc.listConnections("%s.ikfk" % paramNode, d=True)
        if len(connections) == 1:
            paramNode = connections[0]

        valueCurrent =  mc.getAttr("%s.ikfk" % (paramNode))
        value = mc.getAttr("%s.ikfk_switch" % (paramNode))
        if valueCurrent != value:
            switch(paramNode, value)
    except:
        # print error -mjs
        print 'ikfk switch - Can not run the switch'
        print '-'*100
        traceback.print_exc()
        print '-'*100
        print 'ikfk switch - Can not run the switch'
    mc.undoInfo(closeChunk=1)

def legSwitch():
    '''
    '''
    mc.undoInfo(openChunk=1)
    try:
        paramNode = mc.ls(sl=1)[0]

        connections = mc.listConnections("%s.ikfk" % paramNode, d=True)
        if len(connections) == 1:
            paramNode = connections[0]

        namespace=""
        namespaceSplit = paramNode.split(":")

        if len(namespaceSplit) > 1:
            namespace = ":".join(namespaceSplit[:-1]) 
            namespace = "%s:" % (namespace)

        value = mc.getAttr("%s.ikfk_switch" % (paramNode))

        if value == 1:
            fkControl = eval(mc.getAttr("%s.footFkControl" % (paramNode)))
            fkControlPos = mc.xform("%s%s" % (namespace, fkControl), q=True, ws=True, matrix=True)
            switch(paramNode, value)
            mc.xform("%s%s" % (namespace, fkControl), ws=True, matrix=fkControlPos)
        elif value == 0:
            footIkControls = eval(mc.getAttr(paramNode + '.footIkControls'))
            for ctrl in footIkControls:
                attrs = mc.listAttr("%s%s" % (namespace, ctrl), ud=False, keyable=True)
                for attr in attrs:
                    try:
                        mc.setAttr("%s%s.%s" % (namespace,ctrl, attr), 0.0)
                    except:
                        pass

            switch(paramNode, value)
    except:
        # print error -mjs
        print 'ikfk switch - Can not run the switch'
        print '-'*100
        traceback.print_exc()
        print '-'*100
        print 'ikfk switch - Can not run the switch'
    mc.undoInfo(closeChunk=1)

    
topNodeList = mc.ls(["*${element}", "*:${element}"])  
# kill the jobs first
legParamNodeList = ${leg_param_list}
armParamNodeList = ${arm_param_list}
paramNodeList =  legParamNodeList + armParamNodeList
for job in mc.scriptJob(lj=True):
    jobSplit = job.split()
    for node in topNodeList:
        nameSplit = node.split(":")
        name = nameSplit[0]
        for paramNode in paramNodeList:
            jobNameList = ['%s"' % ("%s:%s.ikfk_switch" % (name, paramNode)),
                           '%s.ikfk_switch' % (paramNode),
                           ]
            for jobName in jobNameList:
                for job in jobSplit:
                    if jobName in job:
                        mc.scriptJob(k=int(jobSplit[0].split(":")[0]))    
                        break

for node in topNodeList:
    nameSplit = node.split(":")
    lenSplit = len(nameSplit)
    for paramNode in paramNodeList:
        if lenSplit > 1:
            name = nameSplit[0]
            if paramNode in legParamNodeList:
                mc.scriptJob(attributeChange=["%s:%s.ikfk_switch" % (name, paramNode), legSwitch])            
            elif paramNode in armParamNodeList:
                mc.scriptJob(attributeChange=["%s:%s.ikfk_switch" % (name, paramNode), armSwitch])                            
        else:
            if paramNode in legParamNodeList:
                mc.scriptJob(attributeChange=["%s.ikfk_switch" % (paramNode), legSwitch])            
            elif paramNode in armParamNodeList:
                mc.scriptJob(attributeChange=["%s.ikfk_switch" % (paramNode), armSwitch]) 
"""           
scriptNode = mc.scriptNode(st=1, sourceType="python", bs=cmd, n='ikfkSwitch')
mc.evalDeferred("mc.scriptNode('%s', eb=True)" % scriptNode)
        