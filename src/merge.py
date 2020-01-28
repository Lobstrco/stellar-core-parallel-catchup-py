#!/usr/bin/env python

from __future__ import absolute_import, division, print_function, unicode_literals

import os
import subprocess  # noqa S404
from subprocess import PIPE, Popen  # noqa S404
from time import sleep

from utils.configs import get_jobs_config
from utils.constants import db_history_tables, db_state_tables, merged_path
from utils.db import execute_db_command
from utils.jobs import Job, ResultJob
from utils.logger import logger
from utils.settings import db_host, db_password, db_port, db_user


def get_last_merged_index():
    if not os.path.exists(merged_path):
        return 0

    with open(merged_path, 'r') as merged_file:
        return int(merged_file.read())


def save_last_merged_index(index):
    with open(merged_path, 'w') as merged_file:
        return merged_file.write(str(index))


def wait_job_complete(job):
    while True:
        if job.status != Job.Statuses.completed:
            sleep(10)
            continue
        else:
            break


def check_ledgers(job, result_job):
    if int(job.index) == 1:
        return

    logger.info('Match last hash of result data with previous hash of the first ledger of job {0}'.format(job.index))
    result_ledger = job.start - 1

    result_hash = execute_db_command(
        result_job.db,
        'SELECT ledgerhash FROM ledgerheaders WHERE ledgerseq = {0}'.format(result_ledger),  # noqa S608
        '-t',
    )
    actual_hash = execute_db_command(
        job.db,
        'SELECT prevhash FROM ledgerheaders WHERE ledgerseq = {0}'.format(job.start),  # noqa S608
        '-t',
    )
    if result_hash != actual_hash:
        raise RuntimeError(
            'Last result hash {0} (ledger {1}) does not match previous hash {2} '
            'of first ledger of job {3} (ledger {4})'.format(
                result_hash, result_ledger, job.index, actual_hash, job.start,
            ),
        )


def merge_job_db_history(job, result_job):
    logger.info('Merging job {0} database...'.format(job.index))

    my_env = os.environ.copy()
    my_env['PGPASSWORD'] = db_password

    for table in db_history_tables:
        src_process = Popen([  # noqa S603, S607
            'psql', job.db, '-U', db_user, '-h', db_host, '-p', str(db_port), '-c',
            'COPY (SELECT * FROM {table} WHERE ledgerseq >= {start} AND ledgerseq <= {end}) '  # noqa S608
            'TO STDOUT WITH (FORMAT BINARY)'.format(
                table=table, start=job.start, end=job.end,
            ),
        ], env=my_env, stdout=PIPE)
        dest_process = Popen([  # noqa S603, S607
            'psql', result_job.db, '-U', db_user, '-h', db_host, '-p', str(db_port), '-c',
            'COPY {table} FROM STDIN WITH (FORMAT BINARY)'.format(table=table),
        ], env=my_env, stdin=src_process.stdout, stdout=PIPE)
        src_process.stdout.close()
        out, err = dest_process.communicate()
        if dest_process.returncode != 0:
            raise RuntimeError(err.decode('utf-8'))
        logger.info(out.decode('utf-8'))

    logger.info('Successfully merged job {0} database to the result database.'.format(job.index))


def merge_job_db_state(job, result_job):
    logger.info('Merging state from job {0} to result database...'.format(job.index))

    my_env = os.environ.copy()
    my_env['PGPASSWORD'] = db_password

    for table in db_state_tables:
        logger.info('Copy state: {0}'.format(table))
        src_process = Popen([  # noqa S603, S607
            'psql', job.db, '-U', db_user, '-h', db_host, '-p', str(db_port), '-c',
            'COPY {table} TO STDOUT WITH (FORMAT BINARY)'.format(table=table),
        ], env=my_env, stdout=PIPE)
        dest_process = Popen([  # noqa S603, S607
            'psql', result_job.db, '-U', db_user, '-h', db_host, '-p', str(db_port), '-c',
            'COPY {table} FROM STDIN WITH (FORMAT BINARY)'.format(table=table),
        ], env=my_env, stdin=src_process.stdout, stdout=PIPE)
        src_process.stdout.close()
        out, err = dest_process.communicate()
        if dest_process.returncode != 0:
            raise RuntimeError(err.decode('utf-8'))
        logger.info(out.decode('utf-8'))

    logger.info('Successfully merged state from job {0} to the result database.'.format(job.index))


def merge_job_history(job, result_job):
    logger.info('Merging job {0} history...'.format(job.index))
    subprocess.check_call([  # noqa S603, S607
        'rsync', '-a', job.history_dir + '/', result_job.history_dir + '/',
    ])
    logger.info('Successfully merged job {0} history.'.format(job.index))


def merge_job_state(job, result_job):
    logger.info('Merging job {0} state...'.format(job.index))
    subprocess.check_call('cp -r {0}/* {1}/'.format(job.data_dir, result_job.data_dir), shell=True)  # noqa DU0116, S602
    logger.info('Successfully merged job {0} state.'.format(job.index))


def merge_results():
    last_merged = get_last_merged_index()

    all_jobs = [Job.from_config(config) for config in get_jobs_config().values()]
    all_jobs = sorted(all_jobs, key=lambda job: job.index)
    jobs = list(filter(lambda job: job.index > last_merged, all_jobs))

    result_job = ResultJob()

    for i, job in enumerate(jobs):
        logger.info('Waiting for job {0}'.format(job.index))
        wait_job_complete(job)
        logger.info('Merging job {0}'.format(job.index))

        check_ledgers(job, result_job)
        merge_job_db_history(job, result_job)
        merge_job_history(job, result_job)

        if i + 1 == len(jobs):
            merge_job_db_state(job, result_job)
            merge_job_state(job, result_job)

        save_last_merged_index(job.index)
        job.clean()
