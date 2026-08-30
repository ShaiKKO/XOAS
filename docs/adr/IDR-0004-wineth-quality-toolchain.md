# IDR-0004: Wineth XOAS Quality Toolchain

**Status:** Accepted and verified

**Decision date:** 2026-08-30

**Decision owner:** User / architecture authority

## Context

The physical AMD Target 0 candidate retained Ubuntu 26.04's Python 3.14.4,
Doxygen 1.15.0, and ShellCheck 0.11.0. XOAS requires Python 3.12.3 and Doxygen
1.9.8 exactly, while its accepted shell-policy behavior is bound to ShellCheck
0.9.0. This prevented the complete repository quality suite from configuring
on `wineth-ubuntu`.

IDR-0002 originally rejected installing a second development environment on
the measurement candidate because `gpu-2` already supplied the authoritative
quality lane. The user's explicit 2026-08-30 instruction supersedes that
implementation constraint. It does not change the native qualification-bundle
authority or any Target 0 measurement gate.

## Decision

Install an isolated XOAS quality toolchain below `/opt/xoas/development` while
preserving every Ubuntu system-tool path:

- CPython 3.12.3 is installed below
  `/opt/xoas/development/python-3.12.3`. Only the versioned
  `/usr/local/bin/python3.12` link is added; `/usr/bin/python3` remains Python
  3.14.4.
- Doxygen 1.9.8 is installed below
  `/opt/xoas/development/doxygen-1.9.8`.
- ShellCheck 0.9.0 is installed below
  `/opt/xoas/development/shellcheck-0.9.0`.
- XOAS quality commands prepend the Doxygen and ShellCheck directories to
  `PATH`. They do not replace `/usr/bin/doxygen` or `/usr/bin/shellcheck`.

The versioned CPython environment contains `attrs` 23.2.0, `jsonschema`
4.10.3, `pyrsistent` 0.20.0, and PyYAML 6.0.1. Its standard SSL, SQLite,
compression, readline, DBM, FFI, and Tk modules were imported successfully.

## Provenance

The official CPython 3.12.3 source archive has SHA-256
`56bfef1fdfc1221ce6720e43a661e3eb41785dd914ce99698d8c7896af4bdaa1`,
matching the digest recorded in Python.org's Sigstore bundle. The installed
interpreter has SHA-256
`30550c71fd7f93a9ddfc3989f5c1a50d2ba1e35c0cfa01365d95bbe5a85d4a4c`.

Doxygen was built from upstream signed commit
`c2fe5c3e4986974eb2a97608b24086683502f07f`, the dereferenced
`Release_1_9_8` tag. The installed executable has SHA-256
`821467ded9a988f753bf7c9628821cf892f4a9719a19966131366c40a0f7c4f7`.

ShellCheck came from Ubuntu Noble package `shellcheck_0.9.0-1_amd64.deb`.
The official package-index SHA-256 is
`eadf78f4dfcb1a271f47a9be5e38d124dffe9d4fea74956fab34e8c3e322a854`;
the installed executable matches the accepted development-lane SHA-256
`54dc63164186ad21fb909f5194fb5291f4035c2d2cae04b5680385b8d8fbb73c`.

Eleven CPython development packages were added without package upgrades,
removals, service restarts, or system-Python replacement: `libdb-dev`,
`libdb5.3-dev`, `libgdbm-compat-dev`, `libgdbm-dev`, `libreadline-dev`,
`tcl-dev`, `tcl8.6-dev`, `tk`, `tk-dev`, `tk8.6`, and `tk8.6-dev`.

## Verification

The following selector was active for all complete quality commands:

```bash
export PATH="/opt/xoas/development/doxygen-1.9.8/bin:/opt/xoas/development/shellcheck-0.9.0/usr/bin:$PATH"
```

At clean `main` commit
`93f164cb6caedc6d4da8eca7315ccba9d9c80506` and tree
`721f28e002058f6566c697d23cf76ca80e93ede4`, `wineth-ubuntu` passed:

```bash
cmake --preset dev-debug
cmake --build --preset dev-debug --target quality
ctest --preset dev-debug --output-on-failure
cmake --preset dev-release
cmake --build --preset dev-release --target quality
ctest --preset dev-release --output-on-failure
cmake --build --preset asan-ubsan --target asan-ubsan
```

Both quality aggregates passed their complete 50-test surfaces. Explicit
Debug and Release replays also passed 50/50, and the final isolated
ASan/UBSan replay passed 3/3. Repository policy, formatting, documentation,
Clang-Tidy, warnings, target tooling, and source-clean assertions passed
without suppressions or source changes.

## Consequences and authority boundary

`wineth-ubuntu` can now execute the complete pinned XOAS quality contract in
addition to producing target-native qualification artifacts. This does not
qualify the host, validate campaign evidence, authorize a new campaign or
reboot, admit a numerical baseline, close M0, or make a performance claim.

The historical Target 0 provisioning lock and candidate manifest remain
point-in-time captures. This supplemental development toolchain does not alter
their target hardware identity, installed baseline hashes, or configuration
digest.

## Reversal

Reversal removes only the versioned `/opt/xoas/development` prefixes and the
versioned `/usr/local/bin/python3.12` link after confirming no active XOAS
process uses them. Package removal is a separate administrator decision; do
not remove shared development packages automatically.
