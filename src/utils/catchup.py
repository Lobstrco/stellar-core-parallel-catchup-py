from __future__ import absolute_import, division, print_function, unicode_literals

import subprocess  # noqa S404

from jinja2 import Template

from utils.constants import core_template_path
from utils.logger import logger
from utils.settings import db_host, db_password, db_port, db_user, node_secret_key


def render_template(job):
    with open(core_template_path) as template_file:
        template = Template(template_file.read())

    with open(job.config_filename, 'w') as config:
        config.write(template.render({
            'db_name': job.db,
            'db_user': db_user,
            'db_password': db_password,
            'db_port': db_port,
            'db_host': db_host,
            'node_secret': node_secret_key,
            'job_dir': job.dir,
        }))


def catchup(job):
    render_template(job)
    worker = job.worker

    logger.info('Catching up {0} on {1}: {2} blocks to {3}'.format(job.index, worker.index, job.size, job.end))

    commands = [
        c.format(job=job)
        for c in [
            'stellar-core new-db --conf {job.config_filename}',
            'stellar-core new-hist local --conf {job.config_filename}',
            'stellar-core catchup {job.end}/{job.size} --conf {job.config_filename}',
            'stellar-core publish --conf {job.config_filename}',
        ]
    ]

    for command in commands:
        logger.info(command)
        subprocess.check_call(command, shell=True, cwd=job.data_dir)  # noqa S602

    logger.info('Catch up completed for {0} on {1}.'.format(job.index, worker.index))
