###############################################################################
# Copyright 2019 Alex M.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
###############################################################################

import pytest

from typing import Tuple, Union, Type, List
from .. import ddcci
from ..monitor_control import Monitor, enumerate_vcp

# set to true to run the unit test on your monitors
USE_ATTACHED_MONITORS = True


class UnitTestVCP(ddcci.VCP):

    def open(self):
        pass

    def close(self):
        pass

    def set_vcp_feature(self, code: int, value: int):
        self.monitor[code]["current"] = value

    def get_vcp_feature(self, code: int) -> Tuple[int, int]:
        return self.monitor[code]["current"], self.monitor[code]["maximum"]


def get_vcps() -> List[Type[ddcci.VCP]]:
    if USE_ATTACHED_MONITORS:
        return enumerate_vcp()
    else:
        unit_test_vcp_dict = {
            0x10: {
                "current": 50,
                "maximum": 100,
            },
            0xD6: {
                "current": 1,
                "maximum": 5,
            },
        }
        return [UnitTestVCP(unit_test_vcp_dict)]


@pytest.fixture(scope="module", params=get_vcps())
def monitor(request) -> Type[Monitor]:
    monitor = Monitor(request.param)
    monitor.open()
    yield monitor
    monitor.close()


@pytest.mark.parametrize(
    "luminance, expected",
    [(100, 100), (0, 0), (50, 50), (101, ValueError)]
)
def test_luminance(
        monitor: Type[Monitor],
        luminance: int,
        expected: Union[int, Type[Exception]]):
    original = monitor.luminance
    try:
        if isinstance(expected, int):
            monitor.luminance = luminance
            assert monitor.luminance == expected
        elif isinstance(expected, type(Exception)):
            with pytest.raises(expected):
                monitor.luminance = luminance
        else:
            raise AssertionError("test script needs updating")
    finally:
        monitor.luminance = original


@pytest.mark.skipif(
    USE_ATTACHED_MONITORS,
    reason="not going to turn off your monitors"
)
@pytest.mark.parametrize(
    "mode, expected",
    [
        # always recoverable for real monitors
        ("on", 0x01),
        (0x01, 0x01),
        ("INVALID", KeyError),
        (0x00, ValueError),
        (0x06, ValueError),

        # sometimes recoverable for real monitors
        ("standby", 0x02),
        ("suspend", 0x03),
        ("off_soft", 0x04),

        # rarely recoverable for real monitors
        ("off_hard", 0x05),
    ]
)
def test_get_power_mode(
        monitor: Type[Monitor],
        mode: Union[str, int],
        expected: Union[int, Type[Exception]]):
    if isinstance(expected, (int, str)):
        monitor.power_mode = mode
        power_mode = monitor.power_mode
        if USE_ATTACHED_MONITORS and expected != 0x01:
            # Acer XF270HU empirical testing: monitor reports zero when in any
            # power mode that is not on
            assert power_mode == expected or power_mode == 0x00
        else:
            assert monitor.power_mode == expected
    elif isinstance(expected, type(Exception)):
        with pytest.raises(expected):
            monitor.power_mode = mode
    else:
        raise AssertionError("test script needs updating")
