from __future__ import absolute_import, division, print_function, unicode_literals

import os
import shutil
import subprocess  # noqa S404
from time import sleep

from utils.catchup import catchup, render_template
from utils.configs import get_job, get_jobs_config
from utils.constants import catchup_dir, db_history_tables, db_state_tables, locks_dir
from utils.db import create_db, drop_db, execute_db_command
from utils.files import FileExistsError, write_file_nocreate
from utils.logger import logger
from utils.workers import Worker


class Job:
    def __init__(self, index, start, end):
        self.index = index
        self.dir = os.path.join(catchup_dir, self.name)
        self.db = 'catchup-stellar-{0}'.format(self.name)
        self.start = start
        self.end = end
        self.size = end - start

    @classmethod
    def from_config(cls, config):
        return cls(config['index'], config['start'], config['end'])

    @property
    def name(self):
        return 'job-{0}'.format(self.index)

    @classmethod
    def get_completed_filename(cls, index):
        return os.path.join(locks_dir, 'job-{0}-completed'.format(index))

    @classmethod
    def get_worker_filename(cls, index):
        return os.path.join(locks_dir, 'job-{0}-worker'.format(index))

    @property
    def completed_filename(self):
        return self.get_completed_filename(self.index)

    @property
    def worker_filename(self):
        return self.get_worker_filename(self.index)

    @property
    def config_filename(self):
        return os.path.join(self.dir, 'stellar-core.cfg')

    @property
    def data_dir(self):
        return os.path.join(self.dir, 'data')

    @property
    def history_dir(self):
        return os.path.join(self.dir, 'vs')

    def is_started(self):
        return os.path.exists(self.worker_filename)

    @property
    def worker(self):
        if not self.is_started:
            return

        with open(self.worker_filename, 'r') as worker_file:
            try:
                index = int(worker_file.read())
            except ValueError:
                return

        return Worker(index)

    class Statuses:
        completed = 'completed'
        started = 'started'
        failed = 'failed'
        waiting = 'waiting'

    @property
    def status(self):
        if os.path.exists(self.completed_filename):
            return self.Statuses.completed

        if self.is_started():
            if self.worker.is_alive():
                return self.Statuses.started
            else:
                return self.Statuses.failed

        return self.Statuses.waiting

    def clean(self):
        if os.path.exists(self.dir):
            shutil.rmtree(self.dir)
        drop_db(self.db)

    def reset(self):
        if os.path.exists(self.completed_filename):
            os.remove(self.completed_filename)

        if os.path.exists(self.worker_filename):
            os.remove(self.worker_filename)

    @classmethod
    def get_next_job(cls, worker):
        for job_index in get_jobs_config().keys():
            logger.info('Checking job {0}'.format(job_index))
            try:
                write_file_nocreate(cls.get_worker_filename(job_index), str(worker.index))
            except FileExistsError:
                continue

            logger.info('Job {0} is ready to be started.'.format(job_index))

            # double-check that job was not acquired by anyone else
            sleep(1)
            with open(cls.get_worker_filename(job_index), 'r') as worker_file:
                worker_index = int(worker_file.read())

            if worker_index != worker.index:
                logger.info('Job {0} was acquired by {1} instead of {2}'.format(
                    job_index, worker_index, worker.index,
                ))
                continue

            return Job.from_config(get_job(job_index))

        return None

    def initialize_dirs(self):
        for job_dir in [self.dir, self.data_dir, self.history_dir]:
            os.mkdir(job_dir)

    def initialize(self):
        self.initialize_dirs()
        create_db(self.db)

    def catchup(self):
        logger.info('Job {0} catchup'.format(self.index))
        catchup(self)

    def finalize(self):
        with open(self.completed_filename, 'w') as completed_file:
            completed_file.write(str(self.worker.index))

        logger.info('Job {0} finalized'.format(self.index))

    def run(self):
        self.clean()
        self.initialize()
        self.catchup()
        self.finalize()


class ResultJob:
    def __init__(self):
        self.db = 'catchup-stellar-result'
        self.dir = os.path.join(catchup_dir, 'result')

    @property
    def config_filename(self):
        return os.path.join(self.dir, 'stellar-core.cfg')

    @property
    def data_dir(self):
        return os.path.join(self.dir, 'data')

    @property
    def history_dir(self):
        return os.path.join(self.dir, 'vs')

    def prepare_db_structure(self):
        subprocess.check_call(['stellar-core', 'new-db', '--conf', self.config_filename], cwd=self.data_dir)  # noqa S603

        for table in db_state_tables + db_history_tables:
            execute_db_command(self.db, 'DELETE FROM {0}'.format(table))  # noqa S608

    def initialize_db(self):
        drop_db(self.db)
        create_db(self.db)

    def initialize_dirs(self):
        for job_dir in [self.dir, self.data_dir, self.history_dir]:
            os.mkdir(job_dir)

        render_template(self)

    def initialize(self):
        self.initialize_dirs()
        self.initialize_db()
        self.prepare_db_structure()
