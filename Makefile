.PHONY: install test build deploy clean

install:
	pip install -e .
	pip install build twine

test:
	cd tests/js_compat && npm install
	python3 -m unittest discover tests

build: clean
	python3 -m build

deploy: test build
	python3 -m twine upload dist/*

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf src/*.egg-info/
