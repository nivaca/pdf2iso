#!/usr/bin/env bash
# Installs py-pdfconform as a command for this user (Linux):
#
#     ./install.sh               link ~/bin/py-pdfconform (or ~/.local/bin/...)
#     ./install.sh --uninstall   remove that link
#
# The command is a symbolic link to py-pdfconform.py in this folder, so
# the folder must stay where it is; after moving it, run ./install.sh
# again.  The link goes in ~/bin if that folder exists, and otherwise in
# ~/.local/bin (made if need be).  Nothing is copied, and nothing needs
# root.
#
# py-pdfconform: Copyright (C) 2026 Nicolas Vaughan <nicolasvaughan@proton.me>
# SPDX-License-Identifier: GPL-3.0-or-later (see LICENCE.txt)

set -euo pipefail

NAME=py-pdfconform
HERE=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
SCRIPT="$HERE/$NAME.py"

usage() {
    sed -n '2,11s/^# \{0,1\}//p' "${BASH_SOURCE[0]}"
}

die() {
    echo "install.sh: $*" >&2
    exit 1
}

if [[ -d "$HOME/bin" ]]; then
    BIN="$HOME/bin"
else
    BIN="$HOME/.local/bin"
fi
LINK="$BIN/$NAME"

#  Does LINK point to this copy of the script?
points_here() {
    [[ -L "$LINK" ]] && [[ "$(readlink -f -- "$LINK")" == "$(readlink -f -- "$SCRIPT")" ]]
}

install() {
    [[ -f "$SCRIPT" ]] || die "there is no $SCRIPT"
    chmod +x -- "$SCRIPT"
    mkdir -p -- "$BIN"

    if points_here; then
        echo "$LINK already points to $SCRIPT."
    elif [[ -L "$LINK" ]]; then
        echo "Replacing $LINK (it pointed to $(readlink -- "$LINK"))."
        ln -sfn -- "$SCRIPT" "$LINK"
    elif [[ -e "$LINK" ]]; then
        die "$LINK exists and is not a link; remove it first if it can go"
    else
        ln -s -- "$SCRIPT" "$LINK"
        echo "Linked $LINK -> $SCRIPT."
    fi

    case ":$PATH:" in
        *":$BIN:"*) ;;
        *)  echo
            echo "Note: $BIN is not in your PATH, so the shell will not find"
            echo "$NAME yet.  Add it, for example with this line at the end of"
            echo "~/.bashrc (or the file of your shell), and open a new terminal:"
            echo
            echo "    export PATH=\"$BIN:\$PATH\""
            ;;
    esac

    #  Try it: this checks Python and pikepdf (Ghostscript is checked when
    #  a file is converted)
    echo
    if out=$("$LINK" --version 2>&1); then
        echo "Installed: $out.  Try: $NAME --help"
    else
        echo "The link is in place, but the program does not start yet:"
        echo "$out" | sed 's/^/    /'
        if command -v uv >/dev/null 2>&1; then
            echo "uv is installed: 'uv run $SCRIPT' works with a Python of its own."
        fi
        exit 1
    fi
}

uninstall() {
    if points_here; then
        rm -- "$LINK"
        echo "Removed $LINK."
    elif [[ -e "$LINK" || -L "$LINK" ]]; then
        die "$LINK does not point to this copy ($SCRIPT); left alone"
    else
        echo "There is no $LINK; nothing to do."
    fi
}

case "${1:-}" in
    "")                install ;;
    --uninstall)       uninstall ;;
    -h|--help)         usage ;;
    *)                 usage >&2; exit 2 ;;
esac
