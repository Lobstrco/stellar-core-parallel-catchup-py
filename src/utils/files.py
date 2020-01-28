from __future__ import absolute_import, division, print_function, unicode_literals

import errno
import os
import sys

if sys.version_info[0] == 2:
    class FileExistsError(OSError):
        def __init__(self, msg):
            super(FileExistsError, self).__init__(errno.EEXIST, msg)
else:
    FileExistsError = FileExistsError


def write_file_nocreate(name, content):
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY

    try:
        file_handle = os.open(name, flags)
    except OSError as e:
        if e.errno == errno.EEXIST:  # Failed as the file already exists.
            raise FileExistsError('File already exists')
        else:  # Something unexpected went wrong so reraise the exception.
            raise
    else:  # No exception, so the file must have been created successfully.
        with os.fdopen(file_handle, 'w') as file_obj:
            # Using `os.fdopen` converts the handle to an object that acts like a
            # regular Python file object, and the `with` context manager means the
            # file will be automatically closed when we're done with it.
            file_obj.write(content)
