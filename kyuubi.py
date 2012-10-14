import os
import sys
import curses
import logging
import gevent
import collections


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('kyuubi')

TAIL_WINDOW_WIDTH = 100
TAIL_WINDOW_HEIGHT = 15
TAIL_BUFFER_SIZE = 12

LogScreen = collections.namedtuple('LogScreen', 'scrnum logfile screen')


def init_tail(screen, logfile):
    screen.border(0)
    screen.addstr(1, 1, 'TAILING: %s' % logfile, curses.A_BOLD)
    screen.refresh()


def render_buffer(screen, logfile, buffers):
    if buffers:
        screen.clear()
        init_tail(screen, logfile)
        for index, log in enumerate(buffers):
            row = index + 2
            screen.addstr(row, 1, log)
        screen.refresh()


def create_tail(scrnum, logfile):
    window_y = scrnum * TAIL_WINDOW_HEIGHT
    window_x = 0
    screen = curses.newwin(TAIL_WINDOW_HEIGHT, TAIL_WINDOW_WIDTH,
                           window_y, window_x)
    init_tail(screen, logfile)
    return LogScreen(scrnum=scrnum, logfile=logfile, screen=screen)


def tail_watcher(logscreen):
    descriptor = os.open(logscreen.logfile, os.O_RDONLY | os.O_NONBLOCK)
    os.lseek(descriptor, 0, os.SEEK_END)
    buffers = []
    while True:
        lines = os.read(descriptor, 4096).splitlines()
        if not lines:
            gevent.sleep(0.5)
            continue
        else:
            buffers += lines
            if len(buffers) > TAIL_BUFFER_SIZE:
                buffers = buffers[-TAIL_BUFFER_SIZE:]
            render_buffer(logscreen.screen, logscreen.logfile, buffers)
    os.close(descriptor)


def run(screen, logfiles):
    jobs = []
    for index, logfile in enumerate(logfiles):
        if not os.path.exists(logfile):
            continue
        logscreen = create_tail(index, logfile)
        jobs.append(gevent.spawn(tail_watcher, logscreen))
    gevent.joinall(jobs)


if __name__ == "__main__":
    try:
        curses.wrapper(run, sys.argv[1:])
    except KeyboardInterrupt:
        sys.exit(0)
