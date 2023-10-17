#!/usr/bin/env python3
# pylint: disable=missing-class-docstring, too-many-ancestors
# pylint: disable=missing-function-docstring, missing-module-docstring

from functools import wraps
from math import log2
from threading import Thread
from tkinter import Tk, Text, IntVar, Event
from typing import Any, Callable, TypeVar

T = TypeVar("T")


def _updates_screen(func: Callable[..., None]) -> Callable[..., None]:
    @wraps(func)
    def _inner(self, *args, **kwargs) -> None:
        screen.configure(state="normal")
        func(self, *args, **kwargs)
        screen.configure(state="disabled")

    return _inner


class curses:  # pylint: disable=invalid-name
    A_NORMAL = 0
    A_STANDOUT = 2**1
    A_BOLD = 2**2

    COLOR_BLACK = 2**10
    COLOR_RED = 2**11
    COLOR_GREEN = 2**12
    COLOR_YELLOW = 2**13
    COLOR_BLUE = 2**14
    COLOR_MAGENTA = 2**15
    COLOR_CYAN = 2**16
    COLOR_WHITE = 2**17

    # https://www.w3.org/TR/xml-entity-names/025.html
    ACS_RTEE = "⊣"
    ACS_LTEE = "⊢"
    ACS_HLINE = "─"
    ACS_VLINE = "│"
    ACS_URCORNER = "┐"
    ACS_ULCORNER = "┌"
    ACS_LRCORNER = "┘"
    ACS_LLCORNER = "└"

    _color_pairs: list[tuple[int, int]] = [(7, 0)]

    @staticmethod
    def use_default_colors() -> None:
        return

    @staticmethod
    def curs_set(visibility: int) -> None:
        _ = visibility

    @staticmethod
    def _get_usable_color(bit_represented: int) -> int:
        return int(log2(bit_represented) % 10)

    @staticmethod
    def init_pair(pair_number: int, fg: int, bg: int) -> None:
        bg = max(bg, 2**10)
        curses._color_pairs.insert(
            pair_number, (curses._get_usable_color(fg), curses._get_usable_color(bg))
        )

    @staticmethod
    def color_pair(pair_number: int) -> int:
        fg, bg = curses._color_pairs[pair_number]
        return 2 ** (10 + fg) | 2 ** (10 + bg)

    @staticmethod
    def newwin(nlines: int, ncols: int, begin_y: int = 0, begin_x: int = 0):
        return Screen(screen, (ncols, nlines), (begin_y, begin_x))


class _Key:
    def __init__(self, name: str, no_modifiers: int, shift: int = 0) -> None:
        self.name = name
        self.no_modifiers = no_modifiers
        self.shift = shift

    def get(self) -> int:
        return self.no_modifiers

    def get_shift(self) -> int:
        return self.shift


class Screen:
    def __init__(
        self,
        text: Text,
        width_height: tuple[int, int],
        begin_yx: tuple[int, int],
    ) -> None:
        self.screen = text
        self.width = width_height[0]
        self.height = width_height[1]
        self.begin_yx = begin_yx
        self.keys: list[int] = []
        self.keys_len = IntVar()
        self.keys_len.set(0)
        root.bind("<Key>", self._handle_key)

    def __del__(self):
        root.bind("<Key>", stdscr._handle_key)

    def _handle_key(self, event: Event) -> None:
        if self.keys_len.get() > 0 or event.keysym.endswith(("_R", "_L")):
            return
        if event.keysym_num == 99:  # ctrl+c
            raise KeyboardInterrupt()
        # check if state includes modifier(s)
        state = int(event.state)
        # ctrl = (state & 0x4) != 0
        alt = (state & 0x8) != 0 or (state & 0x80) != 0
        shift = (state & 0x1) != 0
        self.keys_len.set(len(self.keys))
        if repr(event.char).startswith("'\\x"):
            self.keys.append(int(repr(event.char)[3:-1], 16))
            return
        special_keys: dict[int, _Key] = {
            23: _Key("Tab", 9, 353),
            36: _Key("Return", 10),
            111: _Key("Up", 259),
            116: _Key("Down", 258),
            119: _Key("Delete", 330),
        }
        if event.keycode in special_keys:
            if shift:
                self.keys.append(special_keys[event.keycode].get_shift())
                return
            self.keys.append(special_keys[event.keycode].get())
            return
        if alt:
            self.keys.append(27)  # escape
            self.keys.append(event.keysym_num)
            self.keys_len.set(len(self.keys))
            return
        self.keys.append(event.keysym_num)

    def getch(self) -> int:
        if len(self.keys) == 0:
            root.wait_variable(self.keys_len)
        self.keys_len.set(len(self.keys) - 1)
        return self.keys.pop(0)

    def _parse_attrs(self, attrs: int) -> list[str]:
        possible_attrs: dict[int, str] = dict(
            (value, name)
            for name, value in dict(curses.__dict__).items()
            if isinstance(value, int)
        )
        possible_returns = {
            "A_BOLD": "bold",
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
        y_pos = self.begin_yx[0] + y
        x_pos = self.begin_yx[1] + x
        self.screen.replace(
            f"{y_pos + 1}.{x_pos}",
            f"{y_pos + 1}.{x_pos + len(text)}",
            text,
            self._parse_attrs(int(bin(attr)[2:])),
        )

    def getmaxyx(self) -> tuple[int, int]:
        return self.height, self.width

    def addch(self, y: int, x: int, char: str, attr: int = 0) -> None:
        self.addstr(y, x, char, attr)

    def nodelay(self, flag: bool = True) -> None:
        _ = flag

    def box(self):
        self.addstr(
            0,
            0,
            curses.ACS_ULCORNER
            + curses.ACS_HLINE * (self.width - 2)
            + curses.ACS_URCORNER,
        )
        for i in range(self.height - 2):
            self.addstr(i + 1, 0, curses.ACS_VLINE)
        for i in range(self.height - 2):
            self.addstr(i + 1, self.width - 1, curses.ACS_VLINE)
        self.addstr(
            self.height - 1,
            0,
            curses.ACS_LLCORNER
            + curses.ACS_HLINE * (self.width - 2)
            + curses.ACS_LRCORNER,
        )

    def hline(self, y: int, x: int, ch: str, n: int) -> None:
        self.addstr(y, x, ch * n)

    def refresh(self) -> None:
        return

    @_updates_screen
    def clear(self) -> None:
        for row in range(self.begin_yx[0] + 1, self.begin_yx[0] + 1 + self.height):
            self.screen.replace(
                f"{row}.{self.begin_yx[1]}",
                f"{row}.{self.width + self.begin_yx[1]}",
                " " * self.width,
            )


root = Tk()
# use multiprocessing
root.protocol("WM_DELETE_WINDOW", root.destroy)
WIDTH = 100
HEIGHT = 30
screen = Text(
    root,
    width=WIDTH,
    height=HEIGHT,
    font="Terminal 12",
    foreground="black",
    background="white",
)
screen.insert(
    f"{0}.{1}",
    "\n".join(WIDTH * " " for _ in range(HEIGHT)),
)
screen.pack()
screen.focus_set()
screen.tag_configure("bold", font="Terminal 12 bold")
screen.tag_configure("black", foreground="black", background="white")
screen.tag_configure("red", foreground="red", background="white")
screen.tag_configure("green", foreground="green", background="white")
screen.tag_configure("yellow", foreground="yellow", background="white")
screen.tag_configure("blue", foreground="blue", background="white")
screen.tag_configure("cyan", foreground="cyan", background="white")
screen.tag_configure("magenta", foreground="magenta", background="white")
screen.tag_configure("white", foreground="black", background="white")
screen.tag_configure("black*", background="black", foreground="white")
screen.tag_configure("red*", background="red", foreground="white")
screen.tag_configure("green*", background="green", foreground="white")
screen.tag_configure("yellow*", background="yellow", foreground="white")
screen.tag_configure("blue*", background="blue", foreground="white")
screen.tag_configure("cyan*", background="cyan", foreground="white")
screen.tag_configure("magenta*", background="magenta", foreground="white")
screen.tag_configure("white*", background="black", foreground="white")
screen.configure(state="disabled")

stdscr = Screen(screen, (WIDTH, HEIGHT), (0, 0))


def wrapper(func: Callable[..., T], *args: list[Any], **kwargs: dict[str, Any]) -> T:
    def worker(q: list[T]):
        q.append(func(stdscr, *args, **kwargs))

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
    if len(result_queue) == 1:
        return result_queue[0]
    raise RuntimeError("tcurses quit unexpectedly")
