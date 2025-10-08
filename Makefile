.PHONY: build-linux clean-linux build-linux-docker

build-linux:
	bash build-linux.sh

clean-linux:
	rm -rf build dist .venv-build-linux

build-linux-docker:
	bash scripts/build_linux_docker.sh
