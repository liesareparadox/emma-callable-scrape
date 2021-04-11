import logging
import os

syslogs_file = 'bin/syslogs.log'


def enable_logger(name):
    logging.basicConfig(format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        level='DEBUG',
                        datefmt='%m-%d %H:%M',
                        filename=syslogs_file,
                        filemode='a')
    #
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    #
    formatter = logging.Formatter('%(levelname)-5s %(message)s')
    #
    console.setFormatter(formatter)

    #
    logging.getLogger(name).addHandler(console)

    log = logging.getLogger(name)

    return log


if __name__ == '__main__':
    pass
