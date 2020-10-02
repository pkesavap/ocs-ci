from os import environ
from ocs_ci.framework.pytest_customization.marks import (
    post_ocp_upgrade, pre_ocs_upgrade, ocp_upgrade
)


@pre_ocs_upgrade
def test_4():
    environ['RH'] += "H"


@post_ocp_upgrade
def test_5():
    environ['RH'] += " "


@ocp_upgrade
def test_6():
    environ['RH'] += "d"
