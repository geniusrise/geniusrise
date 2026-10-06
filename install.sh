#!/bin/sh
set -euo pipefail

repo="geniusrise/geniusrise"
install_dir="${INSTALL_DIR:-$HOME/.local/bin}"

command -v go >/dev/null 2>&1 && echo "note: this installs the release binary, not a go build" || true

os=$(uname -s | tr '[:upper:]' '[:lower:]')
arch=$(uname -m)
case "$arch" in
  x86_64|amd64) arch="amd64" ;;
  aarch64|arm64) arch="arm64" ;;
  *) echo "unsupported architecture: $arch" >&2; exit 1 ;;
esac
case "$os" in
  linux|darwin) ;;
  *) echo "unsupported os: $os (use the zip from releases)" >&2; exit 1 ;;
esac

asset="geniusrise_${os}_${arch}.tar.gz"
url="https://github.com/${repo}/releases/latest/download/${asset}"

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

echo "downloading $url"
curl -fsSL "$url" -o "$tmp/$asset"
tar -xzf "$tmp/$asset" -C "$tmp"

mkdir -p "$install_dir"
mv "$tmp/geniusrise" "$install_dir/geniusrise"
chmod +x "$install_dir/geniusrise"

case ":$PATH:" in
  *":$install_dir:"*) ;;
  *) echo "note: add $install_dir to your PATH" ;;
esac

"$install_dir/geniusrise" --version
echo "installed. start with: geniusrise init"
