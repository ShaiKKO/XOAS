# gpu-2 Development Toolchain v1

**Status:** Exact install intent validated; package installation not started

**Authority:** [`../superpowers/plans/2026-08-28-gpu-2-development-toolchain.md`](../superpowers/plans/2026-08-28-gpu-2-development-toolchain.md)

**Architecture boundary:** [AR-0001 Option 2](../architecture/proposals/AR-0001-target-0-host-qualification.md)

**Capture time:** 2026-08-29T00:58:16Z

**Execution subject:** `ef69e48d4d47cc26fb59999ccc283a835f122c4a`

## Scope

This record identifies the reversible provisioning of XOAS's primary development toolchain on `gpu-2`.
It covers the versioned LLVM compiler/analysis tools and the smallest Ubuntu support-tool set required to implement the approved engineering-quality system.
It excludes benchmark baselines, product/compiler implementation, GPU tooling, a self-hosted CI runner, and any measurement qualification.

## Pre-state

The authenticated host checks established:

- hostname role: `gpu-2`;
- operating system: Ubuntu 24.04.4 LTS, Noble;
- architecture: `amd64`;
- non-interactive administrative boundary: available;
- XOAS LLVM archive keyring path: absent;
- XOAS LLVM APT source path: absent;
- existing APT package holds: none;
- installed package records: 768;
- installed-package pre-state SHA-256: `865058047b8e7d9430cd10fc591f601c9ac6a950f89055543129fd75283a3d0d`;
- Git: 2.43.0;
- Python: 3.12.3;
- curl: 8.5.0;
- GnuPG: 2.4.4.

The server checkout was absent after the collision check.
A clean primary checkout was then created at the non-secret path `$HOME/XOAS` and bound to execution subject `ef69e48d4d47cc26fb59999ccc283a835f122c4a` with the public repository remote and no embedded credentials.

No package, package hold, system compiler alternative, or APT source changed during Task 1.
The only host writes were the clean repository checkout and the mode-0600 temporary installed-package pre-state used for dependency-closure evidence.

## Archive Source State

The XOAS-owned archive keyring and APT source paths were absent at pre-state capture.
Task 2 downloaded the official LLVM archive key from `https://apt.llvm.org/llvm-snapshot.gpg.key`, verified the complete fingerprint, and created only these root-owned mode-0644 files:

| Artifact | Identity |
|---|---|
| Archive key fingerprint | `6084F3CF814B57C1CF12EFD515CF4D18AF4F7421` |
| Keyring SHA-256 | `99f4985fd25cdf4c15b07fd6139d5e205cbd39bab1c65d83484efc92a1d67344` |
| APT source SHA-256 | `8045d768789c700c422e596754817f155032b7dd78ac30a025629007900adb3d` |
| APT source | `deb [signed-by=/usr/share/keyrings/xoas-llvm-archive-keyring.gpg] https://apt.llvm.org/noble/ llvm-toolchain-noble-21 main` |
| Successful metadata refresh | `2026-08-29T01:33:11Z` |
| Observed `clang-21` candidate | `1:21.1.8~++20251221032922+2078da43e25a-1~exp1~20251221153059.70` |

The first metadata-refresh invocation was interrupted after both files were installed.
Recovery inspection found no active APT or dpkg process, verified both file hashes and the key fingerprint, and confirmed the LLVM candidate was available.
A second idempotent `apt-get update` completed without signature, repository, or release-file warnings and produced the timestamp above.

## Rollback Policy

Rollback is an explicit operator action, not an automatic response to a later validation failure.
Before removing packages, the operator must compare the installed dependency closure with the captured pre-state and determine whether later development work depends on it.
Only the two exact XOAS-owned APT paths and the exact reviewed entry-package list may be rollback targets.
The clean `$HOME/XOAS` checkout is retained as the primary development checkout unless the user separately authorizes its removal.

The recorded source-metadata rollback is:

1. unhold only the eight versioned LLVM entry packages if they were held;
2. verify and unlink `/etc/apt/sources.list.d/xoas-llvm-21.list`;
3. verify and unlink `/usr/share/keyrings/xoas-llvm-archive-keyring.gpg`;
4. refresh APT metadata;
5. remove packages only after reviewing the explicit removal simulation and later dependency ownership.

## Stop Conditions

Provisioning stops if:

- the host identity, OS codename, or architecture changes;
- either XOAS-owned system path appears with unexpected content;
- the official LLVM archive fingerprint differs;
- a locked package candidate disappears or changes before installation;
- APT proposes a removal or architecture change;
- a positive probe fails or a negative probe is not detected for its intended reason;
- repository evidence would expose credentials, network coordinates, login identities, or private-key locations.

## Exact Install Intent

The resolved pre-install lock is [`../../toolchains/gpu-2-development-toolchain-v1.lock.json`](../../toolchains/gpu-2-development-toolchain-v1.lock.json), validated by [`../../schemas/development-toolchain-v1.schema.json`](../../schemas/development-toolchain-v1.schema.json).
It records 19 literal package versions from the refreshed cache, 18 expected executable identities, ten required behavioral probes, the APT provenance, rollback pre-state, and `build_ready=false`.

The configuration SHA-256 is `bf49239db2f78403ee592c1d1ddfaebdd7d9597433b6d39bbcfc7d0c4427347a`.
It hashes compact, key-sorted ASCII JSON containing the manifest version, host, archive identity excluding refresh time, ordered requested-package records, ordered expected-binary names, and ordered validation names.
Installation state, timestamps, installed closure, runtime evidence, and binary hashes do not participate in this stable configuration digest.

The pre-install gate produced:

- full draft-2020-12 schema and configuration-digest validation on `gpu-2`;
- exact equality between all 19 locked versions and live APT candidates;
- package-specification SHA-256 `130f7ee9a73aa65503e3992b6533815445a78f2f4c683da6b7cc2100933f3c4b`;
- APT simulation SHA-256 `3457b3192145ba1c9f0605af12fbb2430af6f0b1f87a7b5f820812ee7e5ad0d6`;
- simulation result: zero upgraded, 102 newly installed, zero removed, and 54 not upgraded;
- unchanged `amd64` package architecture;
- no package installation or hold mutation.

## Target 0 Boundary

AR-0001 Option 2 makes `gpu-2` development-only.
No result in this record qualifies it as the Target 0 measurement host or supports a proof-gate, product-class, winning-plan, cache-compatibility, break-even, or performance claim.

## Task Evidence

| Task | State | Evidence |
|---|---|---|
| Task 1 — pre-state | Passed | Host/privilege/path checks, clean checkout, 768-package pre-state, no package holds |
| Task 2 — LLVM source | Passed | Full fingerprint, root-owned path hashes, exact source line, clean APT refresh |
| Task 3 — exact install intent | Passed; commit pending | 19 exact candidates, closed lock/schema, server validation, zero-removal simulation |
| Task 4 — exact installation | Not started | None |
| Task 5 — behavioral probes | Not started | None |
| Task 6 — integration | Not started | None |
