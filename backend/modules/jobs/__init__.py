# Jobs module
from . import pkgdwjob_python

# For backward compatibility, also export as pkgdms_job_python
pkgdms_job_python = pkgdwjob_python

__all__ = ['pkgdwjob_python', 'pkgdms_job_python']

