from __future__ import absolute_import, division, print_function, unicode_literals

import collections
import json
import os

from utils.constants import config_path


def get_config():
    if os.path.exists(config_path):
        with open(config_path, 'r') as config:
            return json.loads(config.read(), object_pairs_hook=collections.OrderedDict)

    return collections.OrderedDict()


def update_config(config):
    with open(config_path, 'w') as config_file:
        config_file.write(json.dumps(config, indent=2))


def add_worker(index):
    config = get_config()
    config['workers'] = list(set(config['workers'] + [index]))
    update_config(config)


def get_workers_config():
    return get_config().get('workers', collections.OrderedDict())


def get_jobs_config():
    return get_config().get('jobs', collections.OrderedDict())


def get_worker(index):
    return get_workers_config()[str(index)]


def get_job(index):
    return get_jobs_config()[str(index)]
