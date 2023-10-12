#!/usr/bin/env python3
# pylint: disable=missing-class-docstring, too-many-ancestors
# pylint: disable=missing-function-docstring, missing-module-docstring

from functools import wraps
from math import sqrt
from threading import Thread
from tkinter import Tk, Text, BooleanVar
from typing import Any, Callable, TypeVar

T = TypeVar("T")


def _updates_screen(func: Callable[..., None]) -> Callable[..., None]:
    @wraps(func)
    def _inner(self, *args, **kwargs) -> None:
        self.screen.configure(state="normal")
        func(self, *args, **kwargs)
        self.screen.configure(state="disabled")

    return _inner


class curses:  # pylint: disable=invalid-name
    A_NORMAL = 0
    A_BOLD = 2**0
    A_STANDOUT = 2**1

    COLOR_BLACK = 2**10
    COLOR_RED = 2**11
    COLOR_GREEN = 2**12
    COLOR_YELLOW = 2**13
    COLOR_BLUE = 2**14
    COLOR_MAGENTA = 2**15
    COLOR_CYAN = 2**16
    COLOR_WHITE = 2**17

    ACS_RTEE = 2**32
    ACS_LTEE = 2**33
    ACS_HLINE = 2**34

    _color_pairs: list[tuple[int, int]] = [(7, 0)]

    @staticmethod
    def use_default_colors() -> None:
        return

    @staticmethod
    def curs_set(visibility: int) -> None:
        _ = visibility

    @staticmethod
    def _get_usable_color(bit_represented: int) -> int:
        return int(sqrt(bit_represented >> 10) + 0.5)

    @staticmethod
    def init_pair(pair_number: int, fg: int, bg: int) -> None:
        bg = max(bg, 0)
        curses._color_pairs.insert(
            pair_number, (curses._get_usable_color(fg), curses._get_usable_color(bg))
        )

    @staticmethod
    def color_pair(pair_number: int) -> int:
        fg, bg = curses._color_pairs[pair_number]
        return 2 ** (10 + fg) | 2 ** (10 + bg)


class Screen:
    def __init__(self, master: Tk) -> None:
        self.root = master
        self.root.bind("<Key>", self._handle_key)
        self.width = 100
        self.height = 30
        self.screen = Text(
            self.root,
            width=self.width,
            height=self.height,
            font="Terminal 12",
            foreground="black",
            background="white",
        )
        self.screen.pack()
        self.screen.focus_set()
        self.screen.tag_configure("bold", font="Terminal 12 bold")
        self.screen.tag_configure("black", foreground="black", background="white")
        self.screen.tag_configure("red", foreground="red", background="white")
        self.screen.tag_configure("green", foreground="green", background="white")
        self.screen.tag_configure("yellow", foreground="yellow", background="white")
        self.screen.tag_configure("blue", foreground="blue", background="white")
        self.screen.tag_configure("cyan", foreground="cyan", background="white")
        self.screen.tag_configure("magenta", foreground="magenta", background="white")
        self.screen.tag_configure("white", foreground="white", background="white")
        self.screen.tag_configure("black*", background="black", foreground="white")
        self.screen.tag_configure("red*", background="red", foreground="white")
        self.screen.tag_configure("green*", background="green", foreground="white")
        self.screen.tag_configure("yellow*", background="yellow", foreground="white")
        self.screen.tag_configure("blue*", background="blue", foreground="white")
        self.screen.tag_configure("cyan*", background="cyan", foreground="white")
        self.screen.tag_configure("magenta*", background="magenta", foreground="white")
        self.screen.tag_configure("white*", background="white", foreground="white")
        self.screen.configure(state="disabled")
        self.key = 0
        self.has_key = BooleanVar()
        self.has_key.set(False)
        self._init_screen()

    def _handle_key(self, event) -> None:
        if self.has_key.get() is False:
            self.key = event.char
            self.has_key.set(True)

    def getch(self) -> int:
        self.root.wait_variable(self.has_key)
        self.has_key.set(False)
        return self.key

    @_updates_screen
    def _init_screen(self) -> None:
        self.screen.insert(
            "1.0", "\n".join(self.width * " " for _ in range(self.height))
        )

    def _parse_attrs(self, attrs: int) -> list[str]:
        possible_attrs: dict[int, str] = dict(
            (value, name)
            for name, value in dict(curses.__dict__).items()
            if isinstance(value, int)
        )
        possible_returns = {
            "A_BOLD": "bold",
            "ACS_RTEE": "⊣",
            "ACS_LTEE": "⊢",
            "ACS_HLINE": "⎯",
            "COLOR_BLACK": "black",
            "COLOR_RED": "red",
            "COLOR_GREEN": "green",
            "COLOR_YELLOW": "yellow",
            "COLOR_BLUE": "blue",
            "COLOR_MAGENTA": "magenta",
            "COLOR_CYAN": "cyan",
            "COLOR_WHITE": "white",
        }
        potential = [
            possible_attrs[2 ** (len(str(attrs)) - 1 - pos)]
            for pos, val in enumerate(str(attrs))
            if val == "1"
        ]
        output = []
        for item in potential:
            if (attrs >> 1) % 2 == 1:  # if attrs ends with 1_, standout
                if item.startswith("COLOR_"):
                    output.append(f"{possible_returns[item]}*")
                continue
            output.append(possible_returns[item])
        return output

    @_updates_screen
    def addstr(self, y: int, x: int, text: str, attr: int = curses.A_NORMAL) -> None:
        self.screen.replace(
            f"{y + 1}.{x}",
            f"{y + 1}.{x + len(text)}",
            text,
            self._parse_attrs(int(bin(attr)[2:])),
        )

    def getmaxyx(self) -> tuple[int, int]:
        return self.height, self.width

    def addch(self, y: int, x: int, char: str, attr: int = 0) -> None:
        self.addstr(y, x, char, attr)

    def nodelay(self) -> None:
        return

    def refresh(self) -> None:
        return

    @_updates_screen
    def clear(self) -> None:
        self.screen.delete("1.0", "end")
        self._init_screen()


def wrapper(func: Callable[..., T], *args: list[Any]) -> T:
    root = Tk()
    stdscr = Screen(root)

    def worker(q: list[T]):
        q.append(func(stdscr, *args))

    def check_thread():
        if not func_thread.is_alive():
            root.quit()
            return
        root.after(100, check_thread)

    result_queue: list[T] = []
    func_thread = Thread(target=worker, args=(result_queue,))
    func_thread.start()
    root.after(100, check_thread)
    root.mainloop()
    func_thread.join()
    return result_queue[0]


def main(stdscr):
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
    stdscr.clear()
    stdscr.addstr(0, 0, "Hello, world!", curses.color_pair(4))
    stdscr.addstr(1, 2, "Bold text", curses.color_pair(2) | curses.A_STANDOUT)
    stdscr.refresh()
    return stdscr.getch()


if __name__ == "__main__":
    wrapper(main)
