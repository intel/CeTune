import os
import sys
import mock
import pytest
from analyzer import *
lib_path = ( os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def test_analyzer():
    #analyzer.main(['--path', '/mnt/data/7-10-fiorbd-randread-4k-qd16-10g-0-60-rbd', 'process_data'])
    process = analyzer.Analyzer('/mnt/data/7-10-fiorbd-randread-4k-qd16-10g-0-60-rbd')
    assert process.dest_dir == '/mnt/data/7-10-fiorbd-randread-4k-qd16-10g-0-60-rbd'
    assert process.get_execute_time() == '2017-05-08 15:20:32'
