#!/usr/bin/env bash
# Rebuild the distributable plugin archive (legacy/bav-pipeline-plugin.zip)
# from the current on-disk plugin payload. Run from the repo root or from
# this script's directory.
#
# Sources now live under legacy/plugin and legacy/skills. The packaged
# archive keeps its historical internal layout: .claude-plugin + skills +
# README.md. It deliberately EXCLUDES automation/ (a clone-time, launchd
# feature installed via legacy/automation/install.sh) and example/. Do not
# widen this scope without reason — and bump the version in
# legacy/plugin/plugin.json BEFORE rebuilding so the packaged manifest
# carries the new version.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

STAGE="$(mktemp -d "${TMPDIR:-/tmp}/bav-plugin-pack.XXXXXX")"
cleanup() { rm -rf "$STAGE"; }
trap cleanup EXIT

mkdir -p "$STAGE/.claude-plugin"
cp "$ROOT/legacy/plugin/plugin.json" "$STAGE/.claude-plugin/plugin.json"
cp -R "$ROOT/legacy/skills" "$STAGE/skills"
cp "$ROOT/README.md" "$STAGE/README.md"

OUT="${1:-$ROOT/legacy/bav-pipeline-plugin.zip}"
rm -f "$OUT"
(
  cd "$STAGE"
  zip -r -X "$OUT" .claude-plugin skills README.md \
    -x '*.DS_Store' -x '*__pycache__*' -x '*.pyc' -x '*~$*' >/dev/null
)

echo "built legacy/bav-pipeline-plugin.zip ($(unzip -l "$OUT" | tail -1 | awk '{print $2}') files)"
echo "version: $(grep -o '\"version\": *\"[^\"]*\"' "$ROOT/legacy/plugin/plugin.json")"
# leak guard: no private-coverage tickers may ship in shipped CODE/DOCS. Evals are
# excluded — their routing-test queries legitimately name real public tickers (e.g.
# "MSFT reported earnings", "value NVDA") and use synthetic ZENW/ACME fixtures. The
# remaining legitimate mentions are generic fiscal-year facts and the "MSFT-style"
# legacy-schema descriptor; anything else (e.g. a CIK map) is a real leak.
leak=0
for fpath in $(unzip -Z1 "$OUT" 'skills/*' | grep -v '/evals/'); do
  if unzip -p "$OUT" "$fpath" 2>/dev/null \
       | grep -nE "\b(MU|MSFT|NVDA|AMD)\b" \
       | grep -vEi 'jun 30|late jan|late sep|MSFT-style' >/dev/null; then
    echo "WARNING: possible private-ticker reference in $fpath — inspect before publishing" >&2
    leak=1
  fi
done
[ "$leak" -eq 0 ] && echo "leak guard: clean (private tickers only in eval routing-queries / fiscal facts)"
