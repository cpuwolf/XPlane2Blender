"""Empty-scene guard for the wiper-bake row of the X-Plane Render panel.

`RENDER_PT_xplane.draw()` emits its button through `row.operator(...)`, and
Blender polls `XPLANE_OT_bake_wiper_gradient_texture` before it draws that
button - so `poll()` runs on every redraw of the panel. Upstream read
`context.active_object.xplane` in both places, which raised

    AttributeError: 'NoneType' object has no attribute 'xplane'

in a scene with no active object - the state a fresh install starts in - and
flooded the console of anyone who opened the Render tab. This script is the
headless half of the regression test: it cannot call the nested
`draw_bake_op()`, so it asserts the operator's poll instead, which is the call
site that actually crashes on redraw.

Run standalone (no add-on install needed):

    blender -b --factory-startup --python tests/poll_guard.test.py

or through the suite, which passes `--addons io_xplane2blender`:

    python tests.py -f poll_guard

Exit code 0 = every path returned without raising.
"""
import importlib
import os
import sys
import traceback

import bpy

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKAGE = os.path.join(REPO, "io_xplane2blender")


def load_this_checkout():
    """Import the add-on from this tree, not from an installed copy.

    `io_xplane2blender` is a top-level name, and the packaged extension unpacks
    a wheel of it into `extensions/.local/lib/pythonX.Y/site-packages`, which
    Blender puts ahead of the repository on sys.path. On a machine that has the
    extension installed, both `--addons io_xplane2blender` (what tests.py
    passes) and a bare import therefore resolve to that older copy - and the
    guard under test would never be the one running.
    """
    loaded = sys.modules.get("io_xplane2blender")
    if loaded is not None:
        where = os.path.dirname(os.path.abspath(loaded.__file__ or ""))
        if where == PACKAGE:
            return loaded
        if hasattr(bpy.types, "EXPORT_OT_xplane_obj"):
            loaded.unregister()
        for name in [
            n for n in sys.modules
            if n == "io_xplane2blender" or n.startswith("io_xplane2blender.")
        ]:
            del sys.modules[name]
    sys.path.insert(0, REPO)
    return importlib.import_module("io_xplane2blender")


io_xplane2blender = load_this_checkout()
print("poll_guard: source under test %s" % io_xplane2blender.__file__)
if not hasattr(bpy.types, "EXPORT_OT_xplane_obj"):
    io_xplane2blender.register()

failures = []

# `bpy.ops...poll()` swallows the exception into a False, which would make this
# script pass on the broken code. Call the classmethod itself: same call site,
# real traceback.
OPERATOR = bpy.types.XPLANE_OT_bake_wiper_gradient_texture


def check(label, call):
    try:
        value = call()
    except Exception:                                  # noqa: BLE001
        failures.append(label)
        print("FAIL %s raised:" % label)
        traceback.print_exc()
        return
    if value:
        failures.append(label)
        print("FAIL %s -> %r (expected falsy)" % (label, value))
        return
    print("ok   %s -> %r" % (label, value))


# 1. The reported crash: no active object at all.
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj)
bpy.context.view_layer.objects.active = None
if bpy.context.active_object is not None:
    sys.exit("poll_guard: could not empty the scene (active object still set)")
check("poll(empty scene)", lambda: OPERATOR.poll(bpy.context))

# 2. An active object that is not an X-Plane export root: the `active is not
#    None and active.xplane.isExportableRoot` branch now evaluates, so a bad
#    guard that only skips the None case would still surface here.
bpy.ops.mesh.primitive_cube_add()
check("poll(non-root mesh active)", lambda: OPERATOR.poll(bpy.context))

# 3. The operator must still be reachable through bpy.ops, i.e. the panel's
#    row.operator() has something to draw.
if bpy.ops.xplane.bake_wiper_gradient_texture.poll():
    failures.append("bpy.ops poll")
    print("FAIL bpy.ops poll -> True in an empty scene")
else:
    print("ok   bpy.ops poll -> False")

if failures:
    print("poll_guard: FAILED (%s)" % ", ".join(failures))
else:
    print("poll_guard: OK")

# tests.py scrapes this line instead of an exit code (see TEST_RESULTS_REGEX
# there); a missing line counts as an unrecoverable error.
print(
    "RESULT: After %d tests got %d errors, 0 failures, and 0 skipped"
    % (3, len(failures))
)
sys.exit(1 if failures else 0)
