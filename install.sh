#!/bin/sh
# Hive in one line, on Linux (Debian/Ubuntu) or macOS:
#   curl -fsSL https://raw.githubusercontent.com/suryanshranjan/hive/main/install.sh | sh
# It installs what Hive needs (git, Python, Node.js, Claude Code), then Hive itself in its own Python environment
# (~/.hive/venv), puts `hive` on your PATH, and tells you the two things left: log in to Claude once, and `hive setup`
# (Telegram, in about two minutes; after that, everything happens on your phone).
# HIVE_FROM=<pip source> installs Hive from elsewhere (tests use a local copy).
set -e
say() { printf '\033[1m%s\033[0m\n' "$*"; }
have() { command -v "$1" >/dev/null 2>&1; }
SUDO=''; [ "$(id -u)" -ne 0 ] && have sudo && SUDO='sudo'
OS=$(uname -s)

say "🐝 Installing Hive"
if [ "$OS" = Darwin ]; then
  have brew || { say "Hive needs Homebrew first: https://brew.sh (one line), then run this again."; exit 1; }
  have git || brew install git
  have python3 || brew install python
  have node || brew install node
elif have apt-get; then
  missing=''
  have git || missing="$missing git"
  have python3 || missing="$missing python3"
  python3 -c 'import venv, ensurepip' 2>/dev/null || missing="$missing python3-venv python3-pip"
  have curl || missing="$missing curl ca-certificates"
  if [ -n "$missing" ]; then
    say "  Installing:$missing"
    $SUDO apt-get update -qq && DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y -qq $missing >/dev/null
  fi
  if ! have node || [ "$(node -p 'process.versions.node.split(".")[0]' 2>/dev/null || echo 0)" -lt 18 ]; then
    say "  Installing Node.js 22"
    curl -fsSL https://deb.nodesource.com/setup_22.x | $SUDO bash - >/dev/null
    DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y -qq nodejs >/dev/null
  fi
else
  say "This installer knows Debian/Ubuntu and macOS. Elsewhere: install git, Python 3.10+, Node.js 18+, then"
  say "  npm install -g @anthropic-ai/claude-code && pip install git+https://github.com/suryanshranjan/hive"
  exit 1
fi
python3 -c 'import sys; sys.exit(sys.version_info < (3, 10))' || { say "Hive needs Python 3.10 or newer."; exit 1; }

if ! have claude; then
  say "  Installing Claude Code"
  npm install -g @anthropic-ai/claude-code >/dev/null 2>&1 || $SUDO npm install -g @anthropic-ai/claude-code >/dev/null
fi

say "  Installing Hive"
mkdir -p "$HOME/.hive"
[ -x "$HOME/.hive/venv/bin/python" ] || python3 -m venv "$HOME/.hive/venv"
"$HOME/.hive/venv/bin/python" -m pip install -q --upgrade pip >/dev/null
"$HOME/.hive/venv/bin/python" -m pip install -q --upgrade "${HIVE_FROM:-git+https://github.com/suryanshranjan/hive}"
mkdir -p "$HOME/.local/bin"
ln -sf "$HOME/.hive/venv/bin/hive" "$HOME/.local/bin/hive"
case ":$PATH:" in *":$HOME/.local/bin:"*) ;; *)
  for rc in "$HOME/.bashrc" "$HOME/.zshrc"; do
    [ -f "$rc" ] && ! grep -q 'HOME/.local/bin' "$rc" && printf '\nexport PATH="$HOME/.local/bin:$PATH"\n' >> "$rc"
  done
  PATH="$HOME/.local/bin:$PATH";;
esac

say ""
say "✅ Hive is installed. Two things left, about three minutes:"
say "  1. claude          (log in to Claude once, then type /exit)"
say "  2. hive setup      (connects your phone through Telegram; after that, talk to Hive there)"
say "Open a new terminal first if 'hive' isn't found."
