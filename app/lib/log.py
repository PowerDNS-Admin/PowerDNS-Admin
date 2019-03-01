import logging

class logger(object):
    def __init__(self, name, level, logfile):
        self.name = name
        self.level = level
        self.logfile = logfile

    def config(self):
        # define logger and set logging level
        logger = logging.getLogger()

        if self.level == 'CRITICAL':
            level = logging.CRITICAL
        elif self.level == 'ERROR':
            level = logging.ERROR
        elif self.level == 'WARNING':
            level = logging.WARNING
        elif self.level == 'DEBUG':
            level = logging.DEBUG
        else:
            level = logging.INFO

        logger.setLevel(level)

        # set request requests module log level
        logging.getLogger("requests").setLevel(logging.CRITICAL)

        if self.logfile:
            # define handler to log into file
            file_log_handler = logging.FileHandler(self.logfile)
            logger.addHandler(file_log_handler)

            # define logging format for file
            file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_log_handler.setFormatter(file_formatter)

        # define handler to log into console
        stderr_log_handler = logging.StreamHandler()
        logger.addHandler(stderr_log_handler)

        # define logging format for console
        console_formatter = logging.Formatter('[%(levelname)s] %(message)s')
        stderr_log_handler.setFormatter(console_formatter)

        return logging.getLogger(self.name)
