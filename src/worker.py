#!/usr/bin/env python

from __future__ import absolute_import, division, print_function, unicode_literals

import sys
from time import sleep

from utils.jobs import Job
from utils.logger import logger
from utils.workers import Worker


def loop(worker):
    job = Job.get_next_job(worker)
    if not job:
        logger.info('Worker {0} finished. No jobs available.'.format(worker.index))
        return True

    logger.info('Worker {0} got job {1}'.format(worker.index, job.index))

    job.run()

    logger.info('Worker {0} finished job {1}'.format(worker.index, job.index))

    return False


def main(index):
    worker = Worker(index)

    logger.info('Worker {0} started'.format(worker.index))

    while True:
        if loop(worker):
            break

        sleep(1)

    logger.info('Worker {0} finished'.format(worker.index))


if __name__ == '__main__':
    main(int(sys.argv[1]))
