import maya.cmds as mc
import openrig.shared.common as common
import maya.mel as mm

#############
# subdivide Duplicate #
#############
def subdivide_duplicate():
    sel = common.getFirstIndex(mc.ls(sl=1, o=1))
    hilight = False
    if not sel:
        sel = common.getFirstIndex(mc.ls(hilite=1, o=1))
    if mc.nodeType(sel) == 'mesh':
        sel = mc.listRelatives(sel, p=1)[0]
    if not sel:
        mc.error('Please select a mesh')

    subdiv = mc.duplicate(sel, n=sel + '_subdiv')[0]
    mc.polySmooth(subdiv)
    subdiv_negative = mc.duplicate(subdiv, n='negative_subdiv')[0]
    mc.select(cl=1)
    mc.blendShape(subdiv, subdiv_negative, sel, w=([0, 1], [1, -1]), tc=0)
    mc.hide(sel)
    mc.delete(subdiv_negative)
    mc.delete(subdiv, ch=1)

    # Add message attribute
    if not mc.objExists(sel + '.subdiv'):
        mc.addAttr(sel, ln='subdiv', at='message')
        mc.addAttr(subdiv, ln='subdiv', at='message')
    mc.connectAttr(sel + '.subdiv', subdiv + '.subdiv', )

    # Add subdiv level attribute
    level = 0
    if not mc.objExists(sel + '.subdivLevel'):
        mc.addAttr(sel, ln='subdivLevel', at='double', dv=level)
        mc.addAttr(subdiv, ln='subdivLevel', at='double', dv=level + 1)
    else:
        level = mc.getAttr(sel + '.subdivLevel')
        mc.setAttr(subdiv + '.subdivLevel', level + 1)

    mc.select(subdiv)

##########
# subdivide TOGGLE #
##########
def subdivide_toggle():
    sel = common.getFirstIndex(mc.ls(sl=1, o=1))
    hilight = False
    if not sel:
        sel = common.getFirstIndex(mc.ls(hilite=1, o=1))
    if mc.nodeType(sel) == 'mesh':
        sel = mc.listRelatives(sel, p=1)[0]
    if not sel:
        mc.error('Please select a mesh')

    if mc.objExists(sel + '.subdiv'):
        otherMesh = common.getFirstIndex(mc.listConnections(sel + '.subdiv'))
        if otherMesh:
            mc.showHidden(otherMesh)
            mc.hide(sel)
            mc.select(otherMesh)

##########
# subdivide COMMIT #
##########
def subdivide_commit():
    sel = common.getFirstIndex(mc.ls(sl=1, o=1))
    if not sel:
        sel = common.getFirstIndex(mc.ls(hilite=1, o=1))
    if mc.nodeType(sel) == 'mesh':
        sel = mc.listRelatives(sel, p=1)[0]
    if not sel:
        mc.error('Please select a mesh')

    if mc.objExists(sel + '.subdiv'):
        connectedMesh = common.getFirstIndex(mc.listConnections(sel + '.subdiv'))
        if connectedMesh:

            connectedMeshCount = mc.polyEvaluate(connectedMesh, v=1)
            selCount = mc.polyEvaluate(sel, v=1)

            sourceMesh = connectedMesh
            if connectedMeshCount > selCount:
                sourceMesh = sel
                sel = connectedMesh

            if connectedMesh:
                mc.delete(sourceMesh, ch=1)
                mc.delete(sel)
                mc.showHidden(sourceMesh)
                mc.deleteAttr(sourceMesh + '.subdiv')

#################
# Extract Faces #
#################
def extract_faces():
    sel = common.getFirstIndex(mc.ls(sl=1, o=1))
    if not sel:
        mc.error('Please select some faces')

    # Grow selection so we don't get get the border edge points
    mc.polySelectConstraint(pp=1, t=0x0008)
    mm.eval('InvertSelection')
    selFaces = mc.ls(sl=1)

    # Ponts that will be removed from the wrap membership
    pointsToRemove = mc.polyListComponentConversion(selFaces, toVertex=1)

    # Grow again so we get the border faces to delete
    mc.polySelectConstraint(pp=1, t=0x0008)
    selFaces = mc.ls(sl=1)

    # Dup
    part = mc.duplicate(sel, n=sel + '_part')[0]

    # Delete faces on dup
    facesToDelete = list()
    selTransform = mc.listRelatives(sel, p=1)[0]
    for x in selFaces:
        geo, index = x.split('.')
        if geo == selTransform:
            facesToDelete.append(part + '.' + index)

    mc.delete(facesToDelete)

    # Build Wrap
    mc.select(sel, part)
    # From C:/Program Files/Autodesk/Maya2018/scripts/others/performCreateWrap.mel
    exclusiveBind = '1'
    wrap = mm.eval('doWrapArgList "7" { "1","0","1", "2", "' + exclusiveBind + '", "1", "0", "0" }')[0]
    set = mc.listConnections(wrap + '.message')[0]
    mc.sets(pointsToRemove, remove=set)

    # Add message attribute
    if not mc.objExists(sel + '.part'):
        mc.addAttr(part, ln='part', at='message')
        mc.addAttr(sel, ln='part', at='message')
        mc.addAttr(sel, ln='partBaseMesh', at='message')
    mc.connectAttr(sel + '.part', part + '.part', )

    # Base mesh
    base = mc.listConnections(wrap + '.basePoints[0]')[0]
    mc.connectAttr(base + '.message', sel + '.partBaseMesh')

    # Hide
    mc.select(part)
    mc.hide(sel)

#################
# Extract commit #
#################

def extract_commit():
    sel = common.getFirstIndex(mc.ls(sl=1, o=1))
    if not sel:
        sel = common.getFirstIndex(mc.ls(hilite=1, o=1))
    if mc.nodeType(sel) == 'mesh':
        sel = mc.listRelatives(sel, p=1)[0]
    if not sel:
        mc.error('Please select a mesh')

    if mc.objExists(sel + '.part'):
        connectedMesh = common.getFirstIndex(mc.listConnections(sel + '.part'))
        if connectedMesh:
            connectedMeshCount = mc.polyEvaluate(connectedMesh, v=1)
            selCount = mc.polyEvaluate(sel, v=1)

            sourceMesh = connectedMesh
            if connectedMeshCount < selCount:
                sourceMesh = sel
                sel = connectedMesh

            if connectedMesh:
                mc.delete(sourceMesh, ch=1)
                mc.delete(sel)
                mc.showHidden(sourceMesh)
                base = mc.listConnections(sourceMesh + '.partBaseMesh')
                if base:
                    mc.delete(base)
                mc.deleteAttr(sourceMesh + '.part')
                mc.deleteAttr(sourceMesh + '.partBaseMesh')

#