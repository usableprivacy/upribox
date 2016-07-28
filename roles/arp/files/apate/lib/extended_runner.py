# coding=utf-8
"""This module provides the class ExtendedRunner, which can be used to perfom
additional actions with the daemon context."""
from daemon import runner


class ExtendedRunner(runner.DaemonRunner):
    """This class can be used to perfom additional actions with the daemon context."""

    def __init__(self, app):
        super(self.__class__, self).__init__(app)
        # extend __init__ here
        # do something additional with daemon context
