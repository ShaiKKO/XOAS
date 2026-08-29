#!/usr/bin/env bash

# Install the exact XOAS quality-tool subset on an ephemeral Ubuntu runner.
set -euo pipefail

repository_root=$(git rev-parse --show-toplevel)
lock_path="${repository_root}/toolchains/github-actions-v1.lock.json"
temporary_directory=$(mktemp -d -t xoas-ci-toolchain.XXXXXX)

cleanup() {
  if [[ -d "${temporary_directory}" &&
        "${temporary_directory}" == /tmp/xoas-ci-toolchain.* ]]; then
    find "${temporary_directory}" -type f -delete
    find "${temporary_directory}" -depth -type d -empty -delete
  fi
}
trap cleanup EXIT

source /etc/os-release
test "${VERSION_CODENAME}" = noble
test "$(dpkg --print-architecture)" = amd64

mapfile -t archive_fields < <(
  python3 - "${lock_path}" <<'PY'
import json
import sys
from pathlib import Path

archive = json.loads(Path(sys.argv[1]).read_text())["apt_archive"]
for field in (
    "key_url",
    "key_fingerprint",
    "keyring_sha256",
    "source_line",
    "source_file_sha256",
):
    print(archive[field])
PY
)
key_url=${archive_fields[0]}
key_fingerprint=${archive_fields[1]}
keyring_sha256=${archive_fields[2]}
source_line=${archive_fields[3]}
source_file_sha256=${archive_fields[4]}

curl --fail --location --silent --show-error \
  "${key_url}" --output "${temporary_directory}/llvm.asc"
gpg --batch --show-keys --with-colons \
  "${temporary_directory}/llvm.asc" \
  | awk -F: '$1 == "fpr" { print $10 }' \
  | grep --fixed-strings --line-regexp "${key_fingerprint}" >/dev/null
gpg --batch --dearmor \
  --output "${temporary_directory}/xoas-llvm-archive-keyring.gpg" \
  "${temporary_directory}/llvm.asc"
printf '%s  %s\n' \
  "${keyring_sha256}" \
  "${temporary_directory}/xoas-llvm-archive-keyring.gpg" \
  | sha256sum --check --status

printf '%s\n' "${source_line}" >"${temporary_directory}/xoas-llvm-21.list"
printf '%s  %s\n' \
  "${source_file_sha256}" \
  "${temporary_directory}/xoas-llvm-21.list" \
  | sha256sum --check --status
sudo install -o root -g root -m 0644 \
  "${temporary_directory}/xoas-llvm-archive-keyring.gpg" \
  /usr/share/keyrings/xoas-llvm-archive-keyring.gpg
sudo install -o root -g root -m 0644 \
  "${temporary_directory}/xoas-llvm-21.list" \
  /etc/apt/sources.list.d/xoas-llvm-21.list

mapfile -t locked_packages < <(
  python3 - "${lock_path}" <<'PY'
import json
import sys
from pathlib import Path

lock = json.loads(Path(sys.argv[1]).read_text())
for package in lock["apt_packages"]:
    print(f'{package["name"]}={package["version"]}')
PY
)
sudo apt-get update
sudo env DEBIAN_FRONTEND=noninteractive apt-get install \
  --yes --no-install-recommends --allow-downgrades \
  "${locked_packages[@]}"

python3 - "${lock_path}" <<'PY'
import json
import subprocess
import sys
from pathlib import Path

lock = json.loads(Path(sys.argv[1]).read_text())
for package in lock["apt_packages"]:
    actual = subprocess.run(
        ["dpkg-query", "-W", "-f=${Version}", package["name"]],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    if actual != package["version"]:
        raise RuntimeError(
            f'{package["name"]}: expected {package["version"]}, observed {actual}'
        )

import jsonschema
import yaml

assert jsonschema.__version__
assert yaml.__version__
PY

/usr/bin/clang++-21 --version
/usr/bin/clang-format-21 --version
/usr/bin/clang-tidy-21 --version
/usr/bin/ld.lld-21 --version
/usr/bin/cmake --version
/usr/bin/ninja --version
/usr/bin/doxygen --version
/usr/bin/shellcheck --version
