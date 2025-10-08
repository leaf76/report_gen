#!/usr/bin/env bash
set -euo pipefail

IMAGE_TAG=${IMAGE_TAG:-report-gen-linux-builder:bookworm}
DOCKERFILE=${DOCKERFILE:-Dockerfile.linux-build}
PLATFORM=${PLATFORM:-}

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

if [[ -n "$PLATFORM" ]]; then
  echo "+ Building Docker image (platform=$PLATFORM): $IMAGE_TAG"
  docker buildx build --platform "$PLATFORM" -f "$ROOT_DIR/$DOCKERFILE" -t "$IMAGE_TAG" "$ROOT_DIR"
else
  echo "+ Building Docker image: $IMAGE_TAG"
  docker build -f "$ROOT_DIR/$DOCKERFILE" -t "$IMAGE_TAG" "$ROOT_DIR"
fi

echo "+ Running build inside container"
docker run --rm -t \
  ${PLATFORM:+--platform "$PLATFORM"} \
  -u "$(id -u):$(id -g)" \
  -v "$ROOT_DIR":/workspace \
  -w /workspace \
  "$IMAGE_TAG" \
  bash -lc 'python3 scripts/build_linux.py'

echo "Build complete. Artifacts under dist/linux/report-gen"
