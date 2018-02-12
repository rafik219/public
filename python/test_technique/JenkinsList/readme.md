
Description:
------------

This script is used to list all jobs on jenkins servers configured on config.yaml file.
and get information about specific jobs name.

Python version : python3.5


Example:
--------

1/ python JenkinsList.py -h     => Get information how to use script.

2/ python JenkinsList -c config.yaml info   => List all jobs with last status and URL.

3/ python JenkinsList.py -c config.yaml info "test-mono-pull-request-testviewer"    => Get more information for "test-mono-pull-request-testviewer" job.



