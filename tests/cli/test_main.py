# -*- coding: utf-8 -*-

from taxonopy import get_name, get_version


def test_version(script_runner):
    
    name = get_name()
    expected = f"{name} {get_version()}\n"
    ret = script_runner.run(name, '--version')
    
    assert ret.success
    assert ret.stdout == expected
    assert ret.stderr == ''


def test_version_short(script_runner):
    
    name = get_name()
    expected = f"{name} {get_version()}\n"
    ret = script_runner.run(name, '-v')
    
    assert ret.success
    assert ret.stdout == expected
    assert ret.stderr == ''
