import os
import sys
import mock
import pytest
from conf import common

def test_GetList():
    l1 = common.get_list("/dev/sdb3:/dev/sdz5,/dev/sdc3:/dev/sdz6")
    assert l1 == [["/dev/sdb3", "/dev/sdz5"], ["/dev/sdc3", "/dev/sdz6"]]

    l2 = common.get_list("/dev/sdb1,/dev/sdc1")
    assert l2 == [["/dev/sdb1", ""], ["/dev/sdc1", ""]]
