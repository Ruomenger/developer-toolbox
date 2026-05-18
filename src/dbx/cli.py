"""dbx 主入口：自动发现并注册 commands/ 下的所有子命令组。"""

from __future__ import annotations

import argparse
import importlib
import pkgutil
from typing import TYPE_CHECKING, Protocol, cast

from . import __version__, commands

if TYPE_CHECKING:
    SubParsers = argparse._SubParsersAction[argparse.ArgumentParser]


class _CommandModule(Protocol):
    def register(self, subparsers: SubParsers) -> None: ...


def _discover_groups() -> list[_CommandModule]:
    found: list[_CommandModule] = []
    for info in pkgutil.iter_modules(commands.__path__):
        module = importlib.import_module(f"{commands.__name__}.{info.name}")
        if hasattr(module, "register"):
            found.append(cast(_CommandModule, module))
    return found


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dbx",
        description="开发者工具箱 — 统一的日常开发辅助命令入口",
    )
    parser.add_argument("-V", "--version", action="version", version=f"dbx {__version__}")
    subparsers = parser.add_subparsers(dest="group", metavar="<command>")
    subparsers.required = True

    for module in _discover_groups():
        module.register(subparsers)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 2
    return int(handler(args) or 0)
