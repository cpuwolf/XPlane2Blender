import os

from io_xplane2blender.tests import *

__dirname__ = os.path.dirname(__file__)


class TestParamLightCandela(XPlaneTestCase):
    def test_candela_suffix_is_a_number(self):
        """A param light's INTENSITY may carry X-Plane 12's candela suffix.

        `300000cd` is what this exporter writes for a photometric light and what
        X-Plane 12 writes in its own aircraft files, so it has to parse back:
        the parameters are validated here and echoed verbatim, and the old
        `float("300000cd")` logged "Parameter 4 (300000cd) is not a number" and
        cancelled the whole export - so importing a file this exporter had just
        written produced no .obj at all.
        """
        self.assertExportableRootExportEqualsFixture(
            "Layer 1",
            os.path.join(__dirname__, "fixtures", "test_param_light_candela.obj"),
            {"LIGHT_PARAM"},
            "param_light_candela",
        )
        self.assertLoggerErrors(0)


runTestCases([TestParamLightCandela])
