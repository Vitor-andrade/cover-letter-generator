"""Launcher: the macOS DYLD-fallback decision (pure, no exec/I/O)."""

from __future__ import annotations

import os

from clg.bootstrap.launcher import _DYLD_VAR, _REEXEC_FLAG, _dyld_fallback_update

_BREW = ["/opt/homebrew/lib"]


def test_noop_on_non_macos():
    assert _dyld_fallback_update(platform="linux", env={}, lib_dirs=_BREW) is None


def test_noop_when_already_reexeced():
    env = {_REEXEC_FLAG: "1"}
    assert _dyld_fallback_update(platform="darwin", env=env, lib_dirs=_BREW) is None


def test_noop_when_no_brew_dirs():
    assert _dyld_fallback_update(platform="darwin", env={}, lib_dirs=[]) is None


def test_sets_path_when_unset():
    assert _dyld_fallback_update(platform="darwin", env={}, lib_dirs=_BREW) == "/opt/homebrew/lib"


def test_appends_preserving_existing():
    env = {_DYLD_VAR: "/existing/lib"}
    result = _dyld_fallback_update(platform="darwin", env=env, lib_dirs=_BREW)
    assert result == os.pathsep.join(["/existing/lib", "/opt/homebrew/lib"])


def test_noop_when_dir_already_present():
    env = {_DYLD_VAR: "/opt/homebrew/lib"}
    assert _dyld_fallback_update(platform="darwin", env=env, lib_dirs=_BREW) is None
