from __future__ import absolute_import, division, print_function, unicode_literals

import os
import subprocess  # noqa S404

import psutil

from utils.configs import add_worker, get_workers_config
from utils.constants import locks_dir, logs_dir


class Worker:
    def __init__(self, index):
        self.index = index

    def start(self):
        process = subprocess.Popen(  # noqa S603
            ['nohup', 'python', 'worker.py', str(self.index)],
            stdout=open(os.path.join(logs_dir, 'worker-{0}.log'.format(self.index)), 'a'),
            stderr=open(os.path.join(logs_dir, 'worker-{0}-err.log'.format(self.index)), 'a'),
            preexec_fn=os.setpgrp,
        )
        self.pid = process.pid

    @property
    def pid_file_path(self):
        return os.path.join(locks_dir, 'worker-{0}.pid'.format(self.index))

    @property
    def pid(self):
        with open(self.pid_file_path, 'r') as pid_file:
            return int(pid_file.read())

    @pid.setter
    def pid(self, pid):
        with open(self.pid_file_path, 'w') as pid_file:
            pid_file.write(str(pid))

    def is_alive(self):
        if not self.pid:
            return False

        try:
            process = psutil.Process(self.pid)
            if process.status() == psutil.STATUS_ZOMBIE:
                return False
        except psutil.NoSuchProcess:
            return False

        return True

    @staticmethod
    def spawn():
        workers = get_workers_config()

        if workers:
            worker_index = max(workers) + 1
        else:
            worker_index = 1

        add_worker(worker_index)

        worker = Worker(worker_index)
        worker.start()
