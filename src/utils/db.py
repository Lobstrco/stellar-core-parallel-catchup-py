from __future__ import absolute_import, division, print_function, unicode_literals

import os
import subprocess  # noqa 404
from time import sleep

from utils.logger import logger
from utils.settings import db_host, db_password, db_port, db_user


def wait_db_autovacuum(db_name):
    code = subprocess.call(  # noqa DU0116
        'ps axu | grep "autovacuum" | grep --quiet {0}'.format(db_name),
        shell=True,   # noqa S602
    )

    if code == 0:
        return

    logger.info('Database {0} is busy.'.format(db_name))
    sleep(5)
    wait_db_autovacuum(db_name)


def execute_db_command(db_name, command, *args):
    my_env = os.environ.copy()
    my_env['PGPASSWORD'] = db_password

    return subprocess.check_output(  # noqa S603
        [
            'psql', db_name, '--username', db_user, '--host', db_host,
            '--port', str(db_port), '--command', command,
        ] + list(args),
        env=my_env,
    )


def create_db(db_name):
    wait_db_autovacuum(db_name)
    logger.info('Creating database {0}...'.format(db_name))
    execute_db_command('postgres', 'create database "{0}"'.format(db_name))
    logger.info('Database {0} was successfully created.'.format(db_name))


def drop_db(db_name):
    wait_db_autovacuum(db_name)
    logger.info('Removing database {0}...'.format(db_name))
    execute_db_command('postgres', 'drop database if exists "{0}"'.format(db_name))
    logger.info('Database {0} was successfully removed.'.format(db_name))
