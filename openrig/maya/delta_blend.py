"""Reconstructed DeltaBlend"""

import maya.cmds as mc
import openrig.maya.psd as psd

def delta_blend(geo):

    if not mc.objExists(geo):
        return
    PSDtarget = mc.ls(geo)[0]
    subsystemGrp = mc.listRelatives(PSDtarget, parent=True)[0]
    interpTransform = subsystemGrp.replace('_interp', '_driver_poseInterpolator')

    if not mc.objExists(interpTransform):
        interpTransform = interpTransform.replace('_driver_poseInterpolator', '_poseInterpolatorShape')
    interp = psd.getInterp(interpTransform)
    oppositeInterp = None

    if '_l_' in interp:
        oppositeInterp = interp.replace('_l_', '_r_')
        oppositePSDtarget = PSDtarget.replace('_l_', '_r_')
    if '_r_' in interp:
        oppositeInterp = interp.replace('_r_', '_l_')
        oppositePSDtarget = PSDtarget.replace('_r_', '_l_')

    # Create a group to hold all of the targets (orig, noDelta, inheritDelta, linearDelta (result of linear instead of dq skin),
    # deltaMush, tension, MegaDeltaMushTension, noDelta_shrinkwrap, inheritDelta_shrinkwrap, deltaMush_shrinkwrap, expand, contract)
    targetGroup = mc.group(name = PSDtarget + '_TEMP_deltaMush_targets', empty=True)
    mc.setAttr(targetGroup + '.v', 0)

    # Make a copy of the current deltas for later reference
    current = mc.duplicate(PSDtarget, name = PSDtarget + '_current_PSD_target')[0]
    mc.parent(current, targetGroup)

    # Create an "orig" target
    bodyGeoDeformerList = []
    history=mc.listHistory('body_geo')
    for potentialDeformer in history:
        types = mc.nodeType(potentialDeformer, inherited=True)
        if 'geometryFilter' in types:
            bodyGeoDeformerList.append(potentialDeformer)
    for bodyGeoDeformer in bodyGeoDeformerList:
        mc.setAttr(bodyGeoDeformer + '.envelope', 0)
    orig = mc.duplicate('body_geo', name=PSDtarget + '_orig_target')[0]
    mc.parent(orig, targetGroup)
    for bodyGeoDeformer in bodyGeoDeformerList:
        mc.setAttr(bodyGeoDeformer + '.envelope', 1)

    # Create a "noDelta" target
    mc.setAttr('skin_psd.envelope', 0)
    noDelta = mc.duplicate('body_geo', name=PSDtarget + '_noDelta_target')[0]
    mc.parent(noDelta, targetGroup)
    mc.setAttr('skin_psd.envelope', 1)

    # Create an "inheritDelta" target
    psd.disablePose(interp, PSDtarget)
    if oppositeInterp:
        psd.disablePose(oppositeInterp, oppositePSDtarget)
    inheritDelta = mc.duplicate('body_geo', name=PSDtarget + '_inheritDelta_target')[0]
    mc.parent(inheritDelta, targetGroup)
    psd.enablePose(interp, PSDtarget)
    if oppositeInterp:
        psd.enablePose(oppositeInterp, oppositePSDtarget)

    # Create a "linearSkin" (result of linear instead of dq or weightBlended skin) target
    weightType = mc.getAttr('body_geo_skinCluster.skinningMethod')
    mc.setAttr('body_geo_skinCluster.skinningMethod', 0)
    linearSkin = mc.duplicate('body_geo', name=PSDtarget + '_linearSkin_target')[0]
    mc.parent(linearSkin, targetGroup)
    mc.setAttr('body_geo_skinCluster.skinningMethod', weightType)

    # Create a "deltaMush" target
    #
    # Dup the orig shape
    deltaMush = mc.duplicate(orig, name=PSDtarget + '_deltaMush_target')[0]
    # Blendshape the orig into the current
    mc.blendShape(current, deltaMush, w=[(0, 0.0)], name=PSDtarget + '_current_target')
    # make the delta mush
    deltaMush_deformer = mc.deltaMush(deltaMush)[0]
    mc.pointPosition(deltaMush+'.vtx[0]')
    mc.setAttr(PSDtarget + '_current_target.' + current, 1)
    mc.select(deltaMush)
    # Refresh
    mc.pointPosition(current+'.vtx[0]')
    mc.delete(deltaMush, ch=True)

    # Create a "tension" target
    tension = mc.duplicate(orig, name=PSDtarget + '_tension_target')[0]
    mc.blendShape(current, tension, w=[(0, 0.0)], name=PSDtarget + '_current_target')
    tension_deformer = mc.tension(tension, smoothingIterations=10, smoothingStep=1, pinBorderVertices=1)[0]
    for attr in ['.bendStrength', '.inwardConstraint', '.outwardConstraint', '.squashConstraint', '.stretchConstraint', '.relative', '.shearStrength']:
        mc.setAttr(tension_deformer + attr, 1.0)
    mc.pointPosition(tension+'.vtx[0]')
    mc.setAttr(PSDtarget + '_current_target.' + current, 1)
    mc.delete(tension, ch=True)

    # Create a "MegaDeltamushTension" target
    # (deltaMush and tension deformers cranked beyond all reasonable levels)
    mdt = mc.duplicate(orig, name=PSDtarget + '_MegaDeltamushTension_target')[0]
    mc.blendShape(current, mdt, w=[(0, 0.0)], name=PSDtarget + '_current_target')
    deltaMushMDT_deformer = mc.deltaMush(mdt, smoothingIterations=100)[0]
    tensionMDT_deformer = mc.tension(mdt, smoothingIterations=10, smoothingStep=1, pinBorderVertices=1)[0]
    for attr in ['.bendStrength', '.inwardConstraint', '.outwardConstraint', '.squashConstraint', '.stretchConstraint', '.relative', '.shearStrength']:
        mc.setAttr(tensionMDT_deformer + attr, 1.0)
    # light deltamush to get rid of artifacts
    deltaMushMDT_deformer = mc.deltaMush(mdt, smoothingIterations=3)[0]
    mc.pointPosition(mdt+'.vtx[0]')
    mc.setAttr(PSDtarget + '_current_target.' + current, 1)
    mc.delete(mdt, ch=True)

    # Create a "noDelta_shrinkwrap" target
    noDelta_shrinkwrap = mc.duplicate(current, name=PSDtarget + '_noDelta_shrinkwrap_target')[0]
    noDelta_shrinkwrap_deformer = mc.deformer(noDelta_shrinkwrap, type='shrinkWrap', name=PSDtarget + '_noDelta_shrinkwrap_target_shrinkwrap_deformer')[0]
    mc.connectAttr(noDelta + '.worldMesh[0]', noDelta_shrinkwrap_deformer + '.targetGeom')
    mc.setAttr(noDelta_shrinkwrap_deformer + '.projection', 4)
    mc.pointPosition(noDelta_shrinkwrap+'.vtx[0]')
    mc.delete(noDelta_shrinkwrap, ch=True)

    # Create an "orig_shrinkwrap" target
    orig_shrinkwrap = mc.duplicate(current, name=PSDtarget + '_orig_shrinkwrap_target')[0]
    orig_shrinkwrap_deformer = mc.deformer(orig_shrinkwrap, type='shrinkWrap', name=PSDtarget + '_orig_shrinkwrap_target_shrinkwrap_deformer')[0]
    mc.connectAttr(orig + '.worldMesh[0]', orig_shrinkwrap_deformer + '.targetGeom')
    mc.setAttr(orig_shrinkwrap_deformer + '.projection', 4)
    mc.pointPosition(orig_shrinkwrap+'.vtx[0]')
    mc.delete(orig_shrinkwrap, ch=True)

    # Create a "deltaMush_shrinkwrap" target
    deltaMush_shrinkwrap = mc.duplicate(current, name=PSDtarget + '_deltaMush_shrinkwrap_target')[0]
    deltaMush_shrinkwrap_deformer = mc.deformer(deltaMush_shrinkwrap, type='shrinkWrap', name=PSDtarget + '_deltaMush_shrinkwrap_target_shrinkwrap_deformer')[0]
    mc.connectAttr(deltaMush + '.worldMesh[0]', deltaMush_shrinkwrap_deformer + '.targetGeom')
    mc.setAttr(deltaMush_shrinkwrap_deformer + '.projection', 4)
    mc.pointPosition(deltaMush_shrinkwrap+'.vtx[0]')
    mc.delete(deltaMush_shrinkwrap, ch=True)

    # Create an "expand" target
    inflationAmount = 5.0
    expand = mc.duplicate(noDelta, name=PSDtarget + '_expand_target')[0]
    mc.polyMoveVertex( expand + '.vtx[*]', ltz=inflationAmount )
    mc.delete(expand, ch=True)

    # Create a "contract" target
    contract = mc.duplicate(noDelta, name=PSDtarget + '_contract_target')[0]
    mc.polyMoveVertex( contract + '.vtx[*]', ltz=(-1.0 * inflationAmount) )
    mc.delete(contract, ch=True)

    # Rename target meshes for simpler (though likely not unique) blendshape target names
    """TEMPORARY SOLUTION, will error if the names are not unique"""
    rename_dict = {orig:'orig', noDelta:'noDelta', inheritDelta:'inheritDelta', linearSkin:'linearSkin', deltaMush:'deltaMush', tension:'tension', mdt:'MDT', noDelta_shrinkwrap:'noDelta_shrinkwrap', orig_shrinkwrap:'orig_shrinkwrap', deltaMush_shrinkwrap:'deltaMush_shrinkwrap', expand:'expand', contract:'contract'}
    for old_name, new_name in rename_dict.items():
        mc.rename(old_name, new_name)

    # Apply all DeltaBlend targets to PSD target
    mc.blendShape('orig', 'noDelta', 'inheritDelta', 'linearSkin', 'deltaMush', 'tension', 'MDT', 'noDelta_shrinkwrap', 'orig_shrinkwrap', 'deltaMush_shrinkwrap', 'expand', 'contract', PSDtarget, w=[(0, 0.0), (1, 0.0), (2, 0.0), (3, 0.0), (4, 0.0), (5, 0.0), (6, 0.0), (7, 0.0), (8, 0.0), (9, 0.0), (10, 0.0), (11, 0.0)], name=PSDtarget + '_DeltaBlend')

    # Delete temporary nodes
    mc.delete(targetGroup)

    # Re-select PSD target geo
    mc.select(PSDtarget)