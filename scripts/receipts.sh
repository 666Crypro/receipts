#!/usr/bin/env bash
# receipts.sh: seal, reveal and judge Receipts calls from the command line.
#
#   receipts.sh seal    "<public topic>" "<your call>" <revealByDays>
#   receipts.sh reveal  <id> <receipt-file>
#   receipts.sh verdict <id> held|missed
#   receipts.sh show    [<render path>]          e.g. "call/1", "board"
#   receipts.sh hash    "<call>" "<salt>"
#
# Env: KEY (gnokey key name, required for writes), GNOKEY_HOME, REMOTE, CHAINID,
#      RECEIPTS_DIR (where receipt files are kept, default ~/.receipts).
# The call text and salt stay on your machine until you reveal.
set -euo pipefail

PKG="gno.land/r/nym-receipts001/receipts"
REMOTE="${REMOTE:-https://rpc.onyx.testnets.gno.land:443}"
CHAINID="${CHAINID:-onyx-1}"
GNOKEY_HOME="${GNOKEY_HOME:-$HOME/.config/gno}"
RECEIPTS_DIR="${RECEIPTS_DIR:-$HOME/.receipts}"
FEE="${FEE:-100000ugnot}"
GAS="${GAS:-30000000}"

hash() { printf '%s|%s' "$2" "$1" | sha256sum | cut -d' ' -f1; }

tx() { # func args...
  local fn="$1"; shift
  local args=()
  for a in "$@"; do args+=(-args "$a"); done
  if [[ -n "${KEYPASS_FILE:-}" ]]; then
    gnokey maketx call -pkgpath "$PKG" -func "$fn" "${args[@]}" -gas-fee "$FEE" -gas-wanted "$GAS" \
      -broadcast -chainid "$CHAINID" -remote "$REMOTE" -home "$GNOKEY_HOME" -insecure-password-stdin "$KEY" < "$KEYPASS_FILE"
  else
    gnokey maketx call -pkgpath "$PKG" -func "$fn" "${args[@]}" -gas-fee "$FEE" -gas-wanted "$GAS" \
      -broadcast -chainid "$CHAINID" -remote "$REMOTE" -home "$GNOKEY_HOME" "$KEY"
  fi
}

case "${1:-}" in
  hash)
    hash "$2" "$3" ;;
  seal)
    topic="$2"; call="$3"; days="$4"
    salt="$(LC_ALL=C tr -dc 'A-HJ-NP-Za-km-z2-9' </dev/urandom | head -c 16)"
    commitment="$(hash "$call" "$salt")"
    mkdir -p "$RECEIPTS_DIR"; chmod 700 "$RECEIPTS_DIR"
    file="$RECEIPTS_DIR/receipt-${commitment:0:8}.txt"
    printf 'commitment: %s\nsalt: %s\ncall:\n%s' "$commitment" "$salt" "$call" > "$file"; chmod 600 "$file"
    echo "commitment $commitment  (call + salt saved to $file, keep it private)"
    tx Seal "$topic" "$commitment" "$days" ;;
  reveal)
    id="$2"; file="$3"
    salt="$(sed -n 's/^salt: //p' "$file")"
    call="$(sed -n '/^call:$/,$p' "$file" | tail -n +2)"
    echo "re-hash check: $(hash "$call" "$salt")"
    tx Reveal "$id" "$call" "$salt" ;;
  verdict)
    tx Verdict "$2" "$3" ;;
  show)
    gnokey query vm/qrender -data "$PKG:${2:-}" -remote "$REMOTE" | sed '1,/^data: /s/^data: //;/^height: /d' ;;
  *)
    sed -n '2,13p' "$0"; exit 1 ;;
esac
