from __future__ import absolute_import, division, print_function, unicode_literals

import os

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
catchup_dir = os.path.join(root, 'catchup')
logs_dir = os.path.join(catchup_dir, 'logs')
locks_dir = os.path.join(catchup_dir, 'locks')
config_path = os.path.join(catchup_dir, 'config.json')
templates_dir = os.path.join(root, 'templates')
core_template_path = os.path.join(templates_dir, 'stellar-core.cfg')
merged_path = os.path.join(locks_dir, 'last-merged.index')

db_state_tables = [
    'accountdata', 'accounts', 'ban', 'offers', 'peers', 'publishqueue',
    'pubsub', 'scphistory', 'scpquorums', 'storestate', 'trustlines',
]  # todo: why quoruminfo is not available???
db_history_tables = [
    'ledgerheaders', 'txhistory', 'txfeehistory', 'upgradehistory',
]
