# -*- coding: utf-8 -*-
from fabric.api import (
    local, run, env, cd
)

env.hosts = ['afpy@afpy.org']


def build():
    local('cd docs; make html')


def update():
    local('hg push; true')
    with cd('~/AfpySphinx/docs'):
        run('hg pull -u; make html')
