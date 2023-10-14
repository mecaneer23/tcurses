#!/usr/bin/env python3
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring, missing-module-docstring

from src.wrap import wrapper, curses
# import curses


def main(scr):
    curses.use_default_colors()
    for i, color in enumerate(
        [
            curses.COLOR_RED,
            curses.COLOR_GREEN,
            curses.COLOR_YELLOW,
            curses.COLOR_BLUE,
            curses.COLOR_MAGENTA,
            curses.COLOR_CYAN,
            curses.COLOR_WHITE,
        ],
        start=1,
    ):
        curses.init_pair(i, color, -1)
    scr.addstr(10, 1, "Hello, world!", curses.color_pair(4))
    scr.box()
    win = curses.newwin(3, 20, 10, 10)
    win.clear()
    win.box()
    win.addstr(1, 1, "Bold text", curses.color_pair(2))
    # win.clear()
    # win.addstr(1, 1, "Bold text", curses.color_pair(5) | curses.A_STANDOUT)
    return win.getch()


if __name__ == "__main__":
    wrapper(main)
