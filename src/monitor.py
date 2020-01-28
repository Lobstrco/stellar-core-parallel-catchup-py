#!/usr/bin/env python

from __future__ import absolute_import, division, print_function, unicode_literals

from time import sleep

from utils.configs import get_jobs_config, get_workers_config
from utils.jobs import Job
from utils.logger import logger
from utils.workers import Worker


def spawn_missing_workers(num_workers):
    alive = len([
        1 for index in get_workers_config()
        if Worker(index).is_alive()
    ])
    jobs_left = len([
        1 for config in get_jobs_config().values()
        if Job.from_config(config).status in [Job.Statuses.waiting, Job.Statuses.started]
    ])
    workers_to_spawn = max(0, min(num_workers, jobs_left) - alive)

    logger.info('Found {0} waiting jobs. {1} workers alive. Spawning {2} more workers'.format(
        jobs_left, alive, workers_to_spawn,
    ))
    [Worker.spawn() for _ in range(workers_to_spawn)]


def check_jobs():
    jobs = [Job.from_config(config) for config in get_jobs_config().values()]

    if all(job.status == Job.Statuses.completed for job in jobs):
        return True

    for job in jobs:
        if job.status == job.Statuses.failed:
            job.reset()

    return False


def monitor_workers(num_workers):
    while True:
        completed = check_jobs()
        if completed:
            logger.info('Everything completed!')
            break
        spawn_missing_workers(num_workers)
        sleep(10)
