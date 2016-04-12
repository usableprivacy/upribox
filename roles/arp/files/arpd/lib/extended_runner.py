from daemon import runner


class ExtendedRunner(runner.DaemonRunner):
    def __init__(self, app):
        super(self.__class__, self).__init__(app)
        # extend __init__ here
        # do something additional with daemon context