# -*- coding: utf-8 -*-
from fabric import (
    local, run, env, cd
)

env.host = 'afpy@afpy.org'


def build_docs():
    local('hg push; true')
    with cd('~/AfpySphinx/docs'):
        run('hg pull -u; make html')
