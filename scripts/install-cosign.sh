#!/bin/sh
# Install a pinned cosign release (if not already present) and print its path.
# Used by the Jenkins signing and verification stages:  COSIGN=$(scripts/install-cosign.sh)
#
# The binary's SHA-256 is checked against the release's official checksums
# file before it is used - a supply-chain control should not itself be
# installed from an unverified download.
set -eu

COSIGN_VERSION=v2.4.3
DEST_DIR=/tmp/cosign-${COSIGN_VERSION}
COSIGN="${DEST_DIR}/cosign"

if [ ! -x "$COSIGN" ]; then
    mkdir -p "$DEST_DIR"
    base="https://github.com/sigstore/cosign/releases/download/${COSIGN_VERSION}"
    curl -sSfL -o "${DEST_DIR}/cosign-linux-amd64" "${base}/cosign-linux-amd64"
    curl -sSfL -o "${DEST_DIR}/cosign_checksums.txt" "${base}/cosign_checksums.txt"
    (cd "$DEST_DIR" && grep ' cosign-linux-amd64$' cosign_checksums.txt | sha256sum -c - >&2)
    mv "${DEST_DIR}/cosign-linux-amd64" "$COSIGN"
    chmod +x "$COSIGN"
fi

echo "$COSIGN"
