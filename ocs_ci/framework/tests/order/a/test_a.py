from os import environ
from ocs_ci.framework.pytest_customization.marks import (
    post_ocs_upgrade, post_upgrade, ocs_upgrade
)


@post_upgrade
def test_1():
    assert environ['RH'] != "Red Hat"


@post_ocs_upgrade
def test_2():
    environ['RH'] += "T"


@ocs_upgrade
def test_3():
    environ['RH'] += "a"
