from os import environ
from ocs_ci.framework.pytest_customization.marks import (
    pre_ocp_upgrade, pre_upgrade)


@pre_ocp_upgrade
def test_7():
    environ['RH'] += "e"


@pre_upgrade
def test_8():
    environ['RH'] = "R"
