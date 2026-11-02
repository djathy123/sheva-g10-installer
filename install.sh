#!/bin/sh
# SHEVA G10 -- one command, local bundle. Does not authenticate any user account.
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec /usr/bin/env python3 "$SCRIPT_DIR/sheva-install.py" "$@"
