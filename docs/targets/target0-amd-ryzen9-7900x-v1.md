# Target 0 AMD Ryzen 9 7900X Candidate v1

**State:** `candidate_unqualified`

**Performance claim:** none

**Task 3 implementation:** `ee57ff5e4af01fecb11fffd985e376d636560434`

**Controlling plan:**
[`2026-08-29-amd-target0-host-qualification.md`](../superpowers/plans/2026-08-29-amd-target0-host-qualification.md)

## Qualification boundary

This physical x86-64 Linux machine is the designated Target 0 measurement
candidate. It is not yet a measurement authority. The candidate manifest is
[`target0-amd-ryzen9-7900x-v1.json`](../../benchmarks/manifests/target0-amd-ryzen9-7900x-v1.json),
and the only authorized Task 4 provisioning input is
[`target0-amd-ryzen9-7900x-v1.lock.json`](../../toolchains/target0-amd-ryzen9-7900x-v1.lock.json).

The lock is `resolved_not_installed`. No support package or baseline library
was installed, no CPU control was changed, and no reboot occurred during Task
3. APT metadata was refreshed once as the approved version-resolution step.
The checkout created for qualification remained clean at protected planning
commit `60c4eeb2ae91c728486079f170dc7a553699657f`.

## Verified host boundary

The closed read-only capture at `2026-08-29T18:01:12Z` established:

- Ubuntu 26.04 `resolute`, kernel `7.0.0-30-generic`, glibc 2.43, and x86-64;
- bare metal with no detected virtualization boundary;
- AMD Ryzen 9 7900X, family 25, model 97, stepping 2, microcode `0xa60120c`;
- 24 online logical CPUs, 12 physical cores, one socket, one NUMA node, and
  symmetric two-thread SMT pairs;
- TSC as the current clocksource;
- available privileged `cycles` and `instructions` events;
- `amd-pstate-epp`, per-CPU preferred-core ranking, governor/EPP controls,
  boost state, `k10temp`, cache topology, interrupt counters, and load capture;
- non-interactive privileged command availability; and
- an absent `/opt/xoas/target0-v1` prefix.

The closed capture SHA-256 is
`019376b74df12d12129dca2618d215dfcd32ad51cdb0ca06b51b19d0977c0106`.
Its producer is `capture_host.py` at fix commit
`b7371ae1bbc74f4c6482b8ca4422ba9b058cfabd`, with source SHA-256
`b94327e0865ac266a2b040f8887d510aa4138558d92d87c6ab8243d5df08ae7f`.
Access aliases, login identity, credentials, network coordinates, home paths,
and full command-line or environment data are not retained.

## Package pre-state and support-package resolution

The sorted pre-state contains 1,502 exact `name<TAB>version` entries and no
package holds. The complete array is retained in the lock.

| Evidence | SHA-256 |
|---|---|
| Package holds | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| Installed-package pre-state | `c84618dd993eb7daf56218d4e0b631385cab4409814f8e576498bac33e387c09` |
| APT refresh log | `ca45e03f46ead81d71455af2de5bf8150875c8c0fcd9247211cc15ab7b121d46` |
| Exact install simulation | `1fdb67a6407584d214e7e571f22752b686bfd738f9e6e39a6f93f661251d29bf` |

The version-pinned simulation resolved 26 new dependency packages, zero
upgrades, and zero removals.

| Requested package | Candidate | Pre-state |
|---|---|---|
| `build-essential` | `12.12ubuntu2.26.04.2` | installed at candidate |
| `gfortran` | `4:15.2.0-5ubuntu1` | absent |
| `doxygen` | `1.15.0+ds1-1ubuntu3` | absent |
| `graphviz` | `14.1.2-1ubuntu1` | absent |
| `shellcheck` | `0.11.0-2` | absent |
| `hwloc` | `2.13.0-2` | absent |
| `lm-sensors` | `1:3.6.2-2build1` | absent |
| `libnuma-dev` | `2.0.19-1build1` | absent |
| `pkg-config` | `2.5.1-4` | installed at candidate |

Task 4 must stop if any candidate, origin, pre-state digest, host fact,
checkout identity, or prefix-collision result changes.

## Existing build and measurement tools

The lock records resolved paths, version lines, and executable hashes for all
19 required tool probes. The important pre-existing versions are GCC/G++
15.2.0, Clang/Clang++ 21.1.8, CMake 4.2.3, Ninja 1.13.2, Python 3.14.4,
Git 2.53.0, and perf 7.0.12. `taskset`, `numactl`, and `cpupower` are present.
The support-package simulation supplies the currently absent `gfortran`,
Doxygen, Graphviz, ShellCheck, hwloc, and lm-sensors executables.

## Frozen upstream identities

Each source tree was cloned into temporary storage, checked out detached,
matched against its approved remote tag or commit, archived with `git archive
--format=tar`, and left uninstalled.

| Source | Tag | Commit | Archive SHA-256 | License identity | State |
|---|---|---|---|---|---|
| AOCL integration | `AOCL-5.3.2-Submodules` | `2fab7ee97dfce6ebc3cb0522c254a3653429f472` | `7d85cd7641a87c81e2821242f91689860862c80d90069f01c53f575697a902ee` | `LICENSE.txt` / `a7632f4bfa66fdc35b03ce37199dd64cfae5d9a8d190decf4f67d45e4968f87d` | identity only |
| AOCL-BLAS | `5.3.2` | `25cad99a6840855ade0a49871197f48ee0e1d317` | `b4237e5c45999ad738215729b50b20cdcc0e0d687d28d4d5338d5765cf582c8c` | `LICENSE` / `0a09d682aa885b092af218ef73e12a65d9db0f237131fdcd628b762a64586ea4` | resolved, not installed |
| OpenBLAS | `v0.3.34` | `e0166008be8e466242aa76b2ff75ce3f0fbf574a` | `b128a9c596d2f329b5c8aa4700ade6805f845fa40e4593c7537ea25b9f7ab15e` | `LICENSE` / `190b5a9c8d9723fe958ad33916bd7346d96fab3c5ea90832bb02d854f620fcff` | resolved, not installed |
| LIBXSMM | `2.1.0` | `7944bf36cf847c846b3fa0eb194789295e00b624` | `704e32a7a479d3ef8f186d633e46296bfe46b4edd6735e0a04eb531ec7986fc4` | `LICENSE.md` / `e60bc806cb48bb16fe29f5b03f5e33384f13063aa1c217dad62d983e318fba46` | resolved, not installed |
| JITSpMM inspection | none | `85b502a4c6603ecdeabb641b3c45b24a61117a4a` | `124fa52dceecf6961409cb5db74117d0aef42b4251cd918f059b1c3f23485a3f` | missing at pinned revision | adapter and use deferred to M2 |

The pinned JITSpMM tree contains no license or copyright statement. XOAS does
not infer permission, does not build or use that source, and does not remove
JITSpMM from the admitted comparator set. M2 must resolve the license and
adapter boundary before use.

Intel oneMKL is recorded as
`not_installed_pending_M2_applicability_review`. That state does not assert
inapplicability and does not remove oneMKL from the admitted policy.

## Remaining qualification gates

The candidate remains unqualified until all applicable gates close:

1. install the exact support package request and verify its dependency closure;
2. build, test, install, and hash AOCL-BLAS, OpenBLAS, and LIBXSMM below the
   versioned prefix;
3. prove explicit loader coexistence, target dispatch, and one effective
   execution thread;
4. pass independent numerical admission for every baseline adapter;
5. prove the real physical-host measurement session restores exact state;
6. pass non-claiming smoke, PMU, and noise characterization;
7. complete campaign one;
8. obtain separate approval for the exact reboot action;
9. complete campaign two under a distinct boot identity;
10. reconcile both campaigns and complete the accepted review model.

No final compatibility digest is computed here. M1 owns the versioned
canonical binary identity.

## Rollback boundary

The only planned source-built installation root is `/opt/xoas/target0-v1`.
Rollback quarantines that complete prefix to a timestamped sibling path.
Package removal is prohibited without a separate administrator review.
