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

"""The one secret the app keeps: an Open Library sign-in, if you save it.

In the operating system's own credential store -- Windows Credential Manager,
the macOS Keychain, the Secret Service on Linux -- never in a file of ours. A
password written to disk is a password anyone with the disk can read; the point
of not storing it in plain text is not met by scrambling it, because the key to
unscramble would have to sit right next to it. Only the OS keeps a secret
properly, so only the OS is asked to.

If there is no such store -- a stripped Linux box, or keyring not
installed -- then nothing is saved and the app asks every time. That is a
smaller convenience, not a broken feature, and it is never a plaintext
fallback.
"""

import json
import logging

logger = logging.getLogger("katipcelebi")

# One record under one name, holding both halves of the sign-in as JSON. The
# store is a name-to-secret map; the username lives inside the secret so that
# it, too, stays out of any file.
SERVICE = "Katip Celebi - Open Library"
ACCOUNT = "openlibrary"

try:
    import keyring
    import keyring.errors

    _KEYRING = keyring
except Exception:  # noqa: BLE001 - pragma: no cover - keyring absent or backendless
    _KEYRING = None


def can_remember() -> bool:
    """Whether there is a safe place to keep a sign-in on this machine.

    Not merely that keyring imported: on a stripped Linux box with no Secret
    Service it imports fine, but its active backend is the "fail" one, whose
    every call raises. Offering to remember a sign-in the machine cannot keep
    would have the user tick the box and nothing be saved -- so the backend is
    asked, not just the import.
    """
    if _KEYRING is None:
        return False
    try:
        from keyring.backends import fail

        return not isinstance(_KEYRING.get_keyring(), fail.Keyring)
    except Exception:  # noqa: BLE001 - pragma: no cover - no usable backend
        return False


def load():
    """The saved (username, password), or None if nothing is kept."""
    if _KEYRING is None:
        return None
    try:
        stored = _KEYRING.get_password(SERVICE, ACCOUNT)
    except Exception:
        logger.warning("Could not read the credential store", exc_info=True)
        return None
    if not stored:
        return None
    try:
        data = json.loads(stored)
        return data["username"], data["password"]
    except (ValueError, KeyError, TypeError):
        logger.warning("The saved sign-in was not readable")
        return None


def save(username: str, password: str) -> bool:
    """Keep a sign-in for next time. False if there is nowhere safe to."""
    if _KEYRING is None:
        return False
    try:
        _KEYRING.set_password(
            SERVICE,
            ACCOUNT,
            json.dumps({"username": username, "password": password}),
        )
        return True
    except Exception:
        logger.warning("Could not write to the credential store", exc_info=True)
        return False


def forget() -> None:
    """Drop the saved sign-in, if there is one."""
    if _KEYRING is None:
        return
    try:
        _KEYRING.delete_password(SERVICE, ACCOUNT)
    except Exception:
        # Nothing there to delete, most likely. Not worth troubling anyone.
        logger.debug("Nothing to forget in the credential store", exc_info=True)
  01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001

# 01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001
