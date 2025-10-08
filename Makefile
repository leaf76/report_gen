.PHONY: build-linux clean-linux

build-linux:
	bash build-linux.sh

clean-linux:
	rm -rf build dist .venv-build-linux
