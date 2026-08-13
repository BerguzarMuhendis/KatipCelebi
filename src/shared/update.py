# Katip Celebi
# Copyright (C) 2026 farukylmz0550
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import json
from urllib.request import urlopen

REPO_RELEASES_URL = (
    "https://api.github.com/repos/farukylmz0550/KatipCelebi/releases/latest"
)


def parse_version(value: str) -> tuple[int, ...]:
    """Normalize a version string like 2.0 or v2.3.4 into comparable ints."""
    text = value.strip().lower()
    if text.startswith("v"):
        text = text[1:]

    parts: list[int] = []
    for part in text.split("."):
        digits = "".join(ch for ch in part if ch.isdigit())
        if digits:
            parts.append(int(digits))
    return tuple(parts) if parts else (0,)


def _normalize_version_tuple(value: str) -> tuple[int, ...]:
    version = parse_version(value)
    return version + (0,) * max(0, 3 - len(version))


def check_for_update(current_version: str) -> tuple[bool, str, str]:
    """Return (has_update, latest_version, release_url) or (False, current, "")."""
    try:
        with urlopen(REPO_RELEASES_URL, timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception:
        return False, current_version, ""

    tag = payload.get("tag_name") or ""
    url = payload.get("html_url") or ""
    if not tag:
        return False, current_version, ""

    latest = tag.lstrip("v")
    current = current_version.strip().lstrip("v")
    if _normalize_version_tuple(latest) > _normalize_version_tuple(current):
        # Sanity-check the URL to avoid showing arbitrary links.
        if isinstance(url, str) and url.startswith("https://github.com/"):
            return True, latest, url
        return True, latest, ""
    return False, current_version, ""
