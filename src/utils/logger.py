from __future__ import absolute_import, division, print_function, unicode_literals

import logging
import sys

logger = logging.getLogger('parallel-catchup')

out_hdlr = logging.StreamHandler(sys.stdout)
out_hdlr.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
out_hdlr.setLevel(logging.INFO)

logger.addHandler(out_hdlr)
logger.setLevel(logging.INFO)
