#!/usr/bin/env python3
# pylint: disable=missing-class-docstring, too-many-ancestors
# pylint: disable=missing-function-docstring, missing-module-docstring

from enum import Flag
from functools import wraps
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


class curses(Flag):  # pylint: disable=invalid-name
    A_NORMAL = 0
    A_BOLD = 2**0
    A_STANDOUT = 2**1
    ACS_RTEE = 2**2
    ACS_LTEE = 2**3
    ACS_HLINE = 2**4


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
        self.screen.tag_configure("standout", background="black", foreground="white")
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
            (item.value, item.name) for item in list(dict(curses.__members__).values())
        )
        possible_returns = {
            "A_BOLD": "bold",
            "A_STANDOUT": "standout",
            # following two might be flipped
            "ACS_RTEE": "⊢",
            "ACS_LTEE": "⊣",
            "ACS_HLINE": "⎯",
        }
        return [
            possible_returns[possible_attrs[2 ** (len(str(attrs)) - 1 - pos)]]
            for pos, val in enumerate(str(attrs))
            if val == "1"
        ]

    @_updates_screen
    def addstr(self, y: int, x: int, text: str, attr: curses = curses.A_NORMAL) -> None:
        self.screen.replace(
            f"{y + 1}.{x}",
            f"{y + 1}.{x + len(text)}",
            text,
            self._parse_attrs(int(bin(attr.value)[2:])),
        )

    @_updates_screen
    def old_addstr(
        self, y: int, x: int, text: str, attr: curses = curses.A_NORMAL
    ) -> None:
        lines = self.screen.get("1.0", "end").split("\n")
        while len(lines) < y + 1:
            lines.append("")
        lines[y] = lines[y].ljust(x)[:x] + text + lines[y].ljust(x)[x:]
        updated_content = "\n".join(lines)
        self.screen.delete("1.0", "end")
        self.screen.insert(
            "1.0", updated_content, self._parse_attrs(int(bin(attr.value)[2:]))
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
    stdscr.clear()
    stdscr.addstr(0, 10, "Hello, world!")
    stdscr.addstr(1, 2, "Bold text", curses.A_BOLD)
    stdscr.clear()
    stdscr.addstr(0, 12, "Hello, world!")
    stdscr.addstr(1, 22, "Bold text", curses.A_BOLD)
    stdscr.refresh()
    return stdscr.getch()


if __name__ == "__main__":
    wrapper(main)
