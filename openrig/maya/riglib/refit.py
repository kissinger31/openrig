# maya imports
import maya.cmds as mc
import maya.mel as mm
# openrig imports
import openrig.maya.riglib.bindmesh as rig_bindmesh
joint_list = mc.ls('*_bind', type='joint')
point_list = [mc.xform(jnt, q=True, ws=True, t=True) for jnt in joint_list]
'''
geo, follicle_list = rig_bindmesh.create('refit', point_list)
follicle_grp = mc.createNode('transform', n='follicle_grp')
mc.parent(follicle_list, follicle_grp)
'''

for follicle, jnt in zip(follicle_list, joint_list):
    aim_node = mc.createNode('transform', n=jnt.replace('_bind', '_aim'))
    mc.xform(aim_node, ws=True, matrix= mc.xform(follicle, q=True, ws=True, matrix=True))
    mc.parent(aim_node, follicle)
    #mc.pointConstraint(follicle, jnt)

for side in ['_l_']:
    shoulder_aim_cst = mc.aimConstraint('wrist{}aim'.format(side), 'shoulder{}bind'.format(side),
                                        aimVector=(1, 0, 0), upVector=(0, 1, 0), wut="none")[0]
    mm.eval('CBdeleteConnection "elbow{}bind.tz"'.format(side))

    elbow_aim_cst = mc.aimConstraint('wrist{}aim'.format(side), 'elbow{}bind'.format(side),
                                     aimVector=(1, 0, 0), upVector=(0, 1, 0), wut="none")[0]

    thigh_aim_cst = mc.aimConstraint('ankle{}aim'.format(side), 'thigh{}bind'.format(side),
                                     aimVector=(1, 0, 0), upVector=(0, 1, 0), wut="none")[0]
    mm.eval('CBdeleteConnection "knee{}bind.tz"'.format(side))

    knee_aim_cst = mc.aimConstraint('ankle{}aim'.format(side), 'knee{}bind'.format(side),
                                    aimVector=(1, 0, 0), upVector=(0, 1, 0), wut="none")[0]

    # ===================================================
    # Fingers
    # ===================================================
    # index finger
    index_2_aim_cst = mc.aimConstraint('thumb_004{}aim'.format(side), 'thumb_002{}bind'.format(side),
                                       aimVector=(1, 0, 0), upVector=(0, 1, 0), wut="none")[0]
    mm.eval('CBdeleteConnection "thumb_003{}bind.tz"'.format(side))

    # middle finger
    middle_2_aim_cst = mc.aimConstraint('middle_005{}aim'.format(side), 'middle_002{}bind'.format(side),
                                        aimVector=(1, 0, 0), upVector=(0, 1, 0), wut="none")[0]
    mm.eval('CBdeleteConnection "middle_003{}bind.tz"'.format(side))
    mm.eval('CBdeleteConnection "middle_004{}bind.tz"'.format(side))

    # ring finger
    middle_2_aim_cst = mc.aimConstraint('ring_005{}aim'.format(side), 'ring_002{}bind'.format(side),
                                        aimVector=(1, 0, 0), upVector=(0, 1, 0), wut="none")[0]
    mm.eval('CBdeleteConnection "ring_003{}bind.tz"'.format(side))
    mm.eval('CBdeleteConnection "ring_004{}bind.tz"'.format(side))

    # pinky finger
    pinky_2_aim_cst = mc.aimConstraint('pinky_005{}aim'.format(side), 'pinky_002{}bind'.format(side),
                                       aimVector=(1, 0, 0), upVector=(0, 1, 0), wut="none")[0]
    mm.eval('CBdeleteConnection "pinky_003{}bind.tz"'.format(side))
    mm.eval('CBdeleteConnection "pinky_004{}bind.tz"'.format(side))

    # ===================================================
    # toes
    # ===================================================
    for i in (1, 2, 3, 4, 5):
        toe_aim_cst = mc.aimConstraint('toe{}_004{}aim'.format(i, side), 'toe{}_001{}bind'.format(i, side),
                                         aimVector=(1, 0, 0), upVector=(0, 1, 0), wut="none")[0]
        mm.eval('CBdeleteConnection "toe{}_002{}bind.tz"'.format(i, side))
        mm.eval('CBdeleteConnection "toe{}_003{}bind.tz"'.format(i, side))

# spine constraints
spine_0_aim_cst = mc.aimConstraint('spine_1_aim', 'spine_0_bind', aimVector=(1, 0, 0),
                                     upVector=(0, 1, 0), wut="none")[0]
mm.eval('CBdeleteConnection "spine_1_bind.tz"')
spine_1_aim_cst = mc.aimConstraint('spine_2_aim', 'spine_1_bind', aimVector=(1, 0, 0),
                                     upVector=(0, 1, 0), wut="none")[0]
mm.eval('CBdeleteConnection "spine_2_bind.tz"')
spine_2_aim_cst = mc.aimConstraint('spine_3_aim', 'spine_2_bind', aimVector=(1, 0, 0),
                                     upVector=(0, 1, 0), wut="none")[0]
mm.eval('CBdeleteConnection "spine_3_bind.tz"')
spine_3_aim_cst = mc.aimConstraint('spine_4_aim', 'spine_3_bind', aimVector=(1, 0, 0),
                                     upVector=(0, 1, 0), wut="none")[0]
mm.eval('CBdeleteConnection "spine_4_bind.tz"')
spine_4_aim_cst = mc.aimConstraint('spine_5_aim', 'spine_4_bind', aimVector=(1, 0, 0),
                                     upVector=(0, 1, 0), wut="none")[0]
mm.eval('CBdeleteConnection "spine_5_bind.tz"')
spine_5_aim_cst = mc.aimConstraint('chest_aim', 'spine_5_bind', aimVector=(1, 0, 0),
                                     upVector=(0, 1, 0), wut="none")[0]

# neck constraints
neck_base_aim_cst = mc.aimConstraint('skull_aim', 'neck_0_bind', aimVector=(1, 0, 0),
                                     upVector=(0, 1, 0), wut="none")[0]

mm.eval('CBdeleteConnection "neck_0_bind.tz"')
mm.eval('CBdeleteConnection "neck_0_bind.ty"')
mm.eval('CBdeleteConnection "neck_1_bind.tz"')
mm.eval('CBdeleteConnection "neck_1_bind.ty"')
mm.eval('CBdeleteConnection "neck_2_bind.tz"')
mm.eval('CBdeleteConnection "neck_2_bind.ty"')
mm.eval('CBdeleteConnection "neck_3_bind.tz"')
mm.eval('CBdeleteConnection "neck_3_bind.ty"')

def commit():
    mc.delete(mc.ls(type='aimConstraint') + mc.ls(type='pointConstraint'))