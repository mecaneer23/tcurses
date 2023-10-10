#!/usr/bin/env python3
# pylint: disable=missing-class-docstring, too-many-ancestors
# pylint: disable=missing-function-docstring, missing-module-docstring

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


class Screen:
    def __init__(self, master: Tk) -> None:
        self.root = master
        self.root.bind("<Key>", self._handle_key)
        self.width = 100
        self.height = 30
        self.screen = Text(self.root, width=self.width, height=self.height)
        self.screen.pack()
        self.screen.configure(state="disabled")
        self.key = 0
        self.has_key = BooleanVar()
        self.has_key.set(False)

    def _handle_key(self, event) -> None:
        print(f"key {event.char} pressed")
        if self.has_key.get() is False:
            self.key = event.char
            self.has_key.set(True)

    def getch(self) -> int:
        self.root.wait_variable(self.has_key)
        self.has_key.set(False)
        print(f"returning {self.key}")
        return self.key

    @_updates_screen
    def addstr(self, y: int, x: int, text: str, attr: int = 0) -> None:
        y += 1
        x += 1
        current_lines = self.screen.get("1.0", "end").split("\n")
        while len(current_lines) < y:
            current_lines.append("")
        current_lines[y - 1] = current_lines[y - 1].ljust(x - 1)
        current_lines[y - 1] = (
            current_lines[y - 1][: x - 1] + text + current_lines[y - 1][x - 1 :]
        )
        updated_content = "\n".join(current_lines)
        self.screen.delete("1.0", "end")
        self.screen.insert("1.0", updated_content)

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


# def wrapper(func: Callable[..., T], *args: list[Any]) -> T:
#     root = Tk()

#     def check_thread():
#         if func_thread.done():
#             root.destroy()
#         root.after(100, check_thread)

#     # root.title(header)
#     stdscr = Screen(root)
#     with ThreadPoolExecutor() as executor:
#         func_thread = executor.submit(func, stdscr, *args)

#     root.after(100, check_thread)
#     root.mainloop()
#     return func_thread.result()

def wrapper(func: Callable[..., T], *args: list[Any]) -> T:
    root = Tk()
    stdscr = Screen(root)

    def worker(q: list[T]):
        q.append(func(stdscr, *args))

    result_queue = []

    func_thread = Thread(target=worker, args=(result_queue,))
    func_thread.start()

    def check_thread():
        if not func_thread.is_alive():
            root.destroy()
            return
        root.after(100, check_thread)

    root.after(100, check_thread)

    root.mainloop()
    func_thread.join()

    return result_queue[0]


def main(stdscr):
    stdscr.clear()
    stdscr.addstr(0, 1, "Hello, world!")
    stdscr.refresh()
    return stdscr.getch()


if __name__ == "__main__":
    wrapper(main)
