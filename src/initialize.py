#!/usr/bin/env python

from __future__ import absolute_import, division, print_function, unicode_literals

import collections
import os
import shutil

from utils.configs import update_config
from utils.constants import catchup_dir, locks_dir, logs_dir
from utils.jobs import ResultJob


def initialize_structure(start, end, chunk_size):
    if os.path.exists(catchup_dir):
        shutil.rmtree(catchup_dir)

    for folder in [catchup_dir, logs_dir, locks_dir]:
        os.mkdir(folder)

    ResultJob().initialize()

    jobs = collections.OrderedDict()
    for i, chunk_start in enumerate(range(start, end, chunk_size)):
        chunk_end = min(chunk_start + chunk_size - 1, end)
        index = i + 1
        jobs[index] = {
            'index': index,
            'start': chunk_start,
            'end': chunk_end,
        }

    update_config(collections.OrderedDict(jobs=jobs, workers=[]))
