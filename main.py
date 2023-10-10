#!/usr/bin/env python3
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring, missing-module-docstring

from src.wrap import wrapper
# from curses import wrapper


def main(stdscr):
    stdscr.clear()
    stdscr.addstr(0, 1, "Hello, world!")
    stdscr.refresh()
    return stdscr.getch()


if __name__ == "__main__":
    wrapper(main)
