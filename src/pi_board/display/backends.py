from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


class DisplayBackend(Protocol):
    def stop(self) -> None: ...

    def show_single(self, path: Path) -> None: ...

    def start_slideshow(self, *, paths: list[Path], delay_seconds: int, shuffle: bool) -> None: ...


@dataclass
class _BaseBackend:
    state_dir: Path

    @property
    def pid_file(self) -> Path:
        return self.state_dir / "display.pid"

    @property
    def list_file(self) -> Path:
        return self.state_dir / "playlist.txt"

    def _write_list_file(self, paths: list[Path]) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        with self.list_file.open("w", encoding="utf-8") as f:
            for p in paths:
                f.write(str(p) + "\n")

    def _save_pid(self, pid: int) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.pid_file.write_text(str(pid), encoding="utf-8")

    def _read_pid(self) -> int | None:
        try:
            value = self.pid_file.read_text(encoding="utf-8").strip()
            return int(value)
        except Exception:
            return None

    def _kill_pid(self, pid: int) -> None:
        try:
            os.kill(pid, 15)
        except ProcessLookupError:
            return
        except PermissionError:
            return


@dataclass
class DummyBackend(_BaseBackend):
    def stop(self) -> None:
        pid = self._read_pid()
        if pid is not None:
            self._kill_pid(pid)

    def show_single(self, path: Path) -> None:
        self.stop()
        self._save_pid(os.getpid())

    def start_slideshow(self, *, paths: list[Path], delay_seconds: int, shuffle: bool) -> None:
        self.stop()
        self._write_list_file(paths)
        self._save_pid(os.getpid())


@dataclass
class FehBackend(_BaseBackend):
    def stop(self) -> None:
        pid = self._read_pid()
        if pid is not None:
            self._kill_pid(pid)
        subprocess.run(["pkill", "-x", "feh"], stderr=subprocess.DEVNULL)

    def show_single(self, path: Path) -> None:
        self.stop()
        cmd = ["feh", "-Y", "-x", "-Z", "-F", str(path)]
        proc = subprocess.Popen(cmd)
        self._save_pid(proc.pid)

    def start_slideshow(self, *, paths: list[Path], delay_seconds: int, shuffle: bool) -> None:
        self.stop()
        self._write_list_file(paths)
        cmd = ["feh", "-Y", "-x", "-D", str(delay_seconds), "-Z", "-F", "-f", str(self.list_file)]
        if not shuffle:
            # feh defaults to list order; no extra flag needed
            pass
        proc = subprocess.Popen(cmd)
        self._save_pid(proc.pid)


@dataclass
class FbiBackend(_BaseBackend):
    def stop(self) -> None:
        pid = self._read_pid()
        if pid is not None:
            self._kill_pid(pid)
        subprocess.run(["pkill", "-x", "fbi"], stderr=subprocess.DEVNULL)

    def show_single(self, path: Path) -> None:
        self.stop()
        cmd = ["fbi", "-a", "-T", "1", "-noverbose", str(path)]
        proc = subprocess.Popen(cmd)
        self._save_pid(proc.pid)

    def start_slideshow(self, *, paths: list[Path], delay_seconds: int, shuffle: bool) -> None:
        self.stop()
        self._write_list_file(paths)
        cmd = [
            "fbi",
            "-a",
            "-T",
            "1",
            "-t",
            str(delay_seconds),
            "-noverbose",
            "-l",
            str(self.list_file),
        ]
        proc = subprocess.Popen(cmd)
        self._save_pid(proc.pid)
