cmake_minimum_required(VERSION 3.28)

foreach(requiredVariable XOAS_GIT XOAS_PYTHON XOAS_REPOSITORY_ROOT)
  if(NOT DEFINED ${requiredVariable})
    message(FATAL_ERROR "${requiredVariable} is required.")
  endif()
endforeach()

set(markdownScript [=[
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit


RULE = "xoas-markdown-link"
ROOT = Path(sys.argv[1]).resolve()
GIT = sys.argv[2]
INPUT_PATH = sys.argv[3]
LOGICAL_PATH = sys.argv[4]


def tracked_paths():
    output = subprocess.run(
        [GIT, "-C", str(ROOT), "ls-files"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return {entry for entry in output.splitlines() if entry}


def heading_anchors(content):
    anchors = set()
    occurrences = {}
    for line in content.splitlines():
        match = re.match(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$", line)
        if not match:
            continue
        heading = re.sub(r"`([^`]*)`", r"\1", match.group(1))
        heading = re.sub(r"!?\[([^]]*)\]\([^)]*\)", r"\1", heading)
        heading = re.sub(r"<[^>]+>", "", heading)
        slug = heading.strip().lower()
        slug = re.sub(r"[^\w\- ]", "", slug)
        slug = re.sub(r"\s", "-", slug)
        duplicate_index = occurrences.get(slug, 0)
        occurrences[slug] = duplicate_index + 1
        anchors.add(slug if duplicate_index == 0 else f"{slug}-{duplicate_index}")
    return anchors


def destinations(content):
    in_fence = False
    fence_marker = ""
    for line_number, line in enumerate(content.splitlines(), start=1):
        fence = re.match(r"^\s*(```+|~~~+)", line)
        if fence:
            marker = fence.group(1)[0]
            if not in_fence:
                in_fence = True
                fence_marker = marker
            elif marker == fence_marker:
                in_fence = False
            continue
        if in_fence:
            continue
        inspectable = re.sub(r"`[^`]*`", "", line)
        for match in re.finditer(r"!?\[[^]]*\]\(", inspectable):
            destination_start = match.end()
            depth = 1
            escaped = False
            for offset in range(destination_start, len(inspectable)):
                character = inspectable[offset]
                if escaped:
                    escaped = False
                    continue
                if character == "\\":
                    escaped = True
                elif character == "(":
                    depth += 1
                elif character == ")":
                    depth -= 1
                    if depth == 0:
                        yield line_number, inspectable[destination_start:offset].strip()
                        break
            else:
                yield line_number, "<unterminated-inline-destination"
        definition = re.match(r"^\s*\[[^]]+\]:\s*(\S+)", inspectable)
        if definition:
            yield line_number, definition.group(1).strip()


def parse_destination(raw_destination):
    if not raw_destination:
        raise ValueError("empty destination")
    if raw_destination.startswith("<"):
        closing = raw_destination.find(">")
        if closing == -1:
            raise ValueError("unterminated angle-bracket destination")
        target = raw_destination[1:closing]
        suffix = raw_destination[closing + 1 :].strip()
    else:
        pieces = raw_destination.split(maxsplit=1)
        target = pieces[0]
        suffix = pieces[1].strip() if len(pieces) == 2 else ""
    if suffix and not re.fullmatch(r"(?:\"[^\"]*\"|'[^']*'|\([^)]*\))", suffix):
        raise ValueError("malformed optional link title")
    if not target:
        raise ValueError("empty destination")
    return target


def validate_document(actual_path, logical_path, tracked):
    diagnostics = []
    content = actual_path.read_text(encoding="utf-8")
    for line_number, raw_destination in destinations(content):
        location = f"{logical_path}:{line_number}"
        try:
            target = parse_destination(raw_destination)
        except ValueError as error:
            diagnostics.append(f"{RULE}: {location}: {error}")
            continue

        parsed = urlsplit(target)
        if parsed.scheme:
            if parsed.scheme not in {"http", "https", "mailto"}:
                diagnostics.append(
                    f"{RULE}: {location}: unsupported external scheme '{parsed.scheme}'"
                )
            elif parsed.scheme in {"http", "https"} and not parsed.netloc:
                diagnostics.append(f"{RULE}: {location}: external URL has no host")
            elif parsed.scheme == "mailto" and "@" not in parsed.path:
                diagnostics.append(f"{RULE}: {location}: malformed mailto target")
            continue

        if parsed.query:
            diagnostics.append(f"{RULE}: {location}: local targets may not contain queries")
            continue
        if parsed.netloc or parsed.path.startswith("/"):
            diagnostics.append(f"{RULE}: {location}: local target must be repository-relative")
            continue

        decoded_path = unquote(parsed.path)
        target_path = (logical_path.parent / decoded_path).resolve()
        try:
            target_relative = target_path.relative_to(ROOT)
        except ValueError:
            diagnostics.append(f"{RULE}: {location}: target escapes the repository")
            continue

        target_key = target_relative.as_posix()
        if not decoded_path:
            target_path = logical_path
            target_key = logical_path.relative_to(ROOT).as_posix()
        if target_key not in tracked:
            diagnostics.append(f"{RULE}: {location}: target is not tracked: {target_key}")
            continue
        if not target_path.is_file():
            diagnostics.append(f"{RULE}: {location}: target is not a file: {target_key}")
            continue

        if parsed.fragment:
            if target_path.suffix.lower() != ".md":
                diagnostics.append(
                    f"{RULE}: {location}: anchors require a Markdown target"
                )
                continue
            anchor = unquote(parsed.fragment).lower()
            if anchor not in heading_anchors(target_path.read_text(encoding="utf-8")):
                diagnostics.append(
                    f"{RULE}: {location}: missing anchor '#{parsed.fragment}' in {target_key}"
                )
    return diagnostics


tracked = tracked_paths()
documents = []
if INPUT_PATH:
    documents.append((Path(INPUT_PATH), (ROOT / LOGICAL_PATH).resolve()))
else:
    documents.extend(
        (ROOT / relative_path, ROOT / relative_path)
        for relative_path in sorted(tracked)
        if relative_path.lower().endswith(".md")
    )

errors = []
for actual, logical in documents:
    try:
        logical.relative_to(ROOT)
    except ValueError:
        errors.append(f"{RULE}: logical document path escapes the repository: {logical}")
        continue
    errors.extend(validate_document(actual, logical, tracked))

if errors:
    print("\n".join(sorted(errors)), file=sys.stderr)
    sys.exit(1)
]=])

set(markdownInput "")
set(markdownLogicalPath "")
if(DEFINED XOAS_MARKDOWN_INPUT)
  if(NOT DEFINED XOAS_MARKDOWN_LOGICAL_PATH)
    message(FATAL_ERROR
            "XOAS_MARKDOWN_LOGICAL_PATH is required for fixture checks.")
  endif()
  set(markdownInput "${XOAS_MARKDOWN_INPUT}")
  set(markdownLogicalPath "${XOAS_MARKDOWN_LOGICAL_PATH}")
endif()

execute_process(
  COMMAND
    "${XOAS_PYTHON}" -c "${markdownScript}"
    "${XOAS_REPOSITORY_ROOT}" "${XOAS_GIT}"
    "${markdownInput}" "${markdownLogicalPath}"
  RESULT_VARIABLE markdownStatus
  OUTPUT_VARIABLE markdownOutput
  ERROR_VARIABLE markdownError)
string(CONCAT markdownDiagnostics "${markdownOutput}" "${markdownError}")

if(XOAS_MARKDOWN_EXPECT_FAILURE)
  if(markdownStatus EQUAL 0)
    message(FATAL_ERROR "Negative Markdown-link fixture unexpectedly passed.")
  endif()
  if(NOT markdownDiagnostics MATCHES "${XOAS_MARKDOWN_EXPECTED_DIAGNOSTIC}")
    message(FATAL_ERROR
            "Markdown validation failed without the expected diagnostic:\n"
            "${markdownDiagnostics}")
  endif()
  message(STATUS
          "Observed intended Markdown-link rejection: "
          "${XOAS_MARKDOWN_EXPECTED_DIAGNOSTIC}")
  return()
endif()

if(NOT markdownStatus EQUAL 0)
  message(FATAL_ERROR "Markdown-link validation failed:\n${markdownDiagnostics}")
endif()
