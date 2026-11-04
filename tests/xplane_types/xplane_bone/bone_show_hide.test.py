import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender.tests import test_creation_helpers
from io_xplane2blender.tests.test_creation_helpers import (
    DatablockInfo,
    ParentInfo,
    SHOW_ANIM_H,
    SHOW_ANIM_S,
)
from io_xplane2blender.xplane_config import *
from io_xplane2blender.xplane_types import xplane_file

__dirname__ = os.path.dirname(__file__)


class TestBoneShowHide(XPlaneTestCase):
    """A Bone is not a Blender Object, so it never gets an XPlaneObject.

    ANIM_show/ANIM_hide datarefs attached to a bone (bone.xplane.datarefs)
    used to be silently dropped by the exporter. They must be written at the
    bone's own level, wrapping whatever geometry lives underneath it.
    """

    def test_bone_show_hide(self):
        test_creation_helpers.create_initial_test_setup()
        bpy.context.scene.xplane.version = "1100"

        coll = test_creation_helpers.create_datablock_collection("Layer 1")
        arm = test_creation_helpers.create_datablock_armature(
            DatablockInfo("ARMATURE", "Armature", collection=coll)
        )
        test_creation_helpers.create_datablock_mesh(
            DatablockInfo(
                "MESH",
                "Cube",
                parent_info=ParentInfo(arm, "BONE", "Bone"),
                collection=coll,
            )
        )

        bone = arm.data.bones["Bone"]
        test_creation_helpers.set_animation_data(bone, SHOW_ANIM_S, parent_armature=arm)
        bone.xplane.datarefs[0].loop = 5
        test_creation_helpers.set_animation_data(bone, SHOW_ANIM_H, parent_armature=arm)

        out = self.exportExportableRoot("Layer 1")

        def filterLines(line):
            return isinstance(line[0], str) and (
                line[0].startswith("ANIM") or line[0].startswith("TRIS")
            )

        lines = self.parseFileToLines(out)
        anim_lines = [line for line in lines if filterLines(line)]

        self.assertEqual(
            anim_lines,
            [
                ("ANIM_begin",),
                ("ANIM_show", 0.0, 100.0, "show_hide_dataref_show"),
                ("ANIM_keyframe_loop", 5.0),
                ("ANIM_hide", 100.0, 200.0, "show_hide_dataref_hide"),
                ("TRIS", 0.0, 36.0),
                ("ANIM_end",),
            ],
        )


runTestCases([TestBoneShowHide])
