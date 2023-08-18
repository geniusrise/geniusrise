
setup:
	@pip install -r ./requirements.txt

developer-setup:
	@pip install -r ./requirements.txt
	@pip install -r ./requirements-dev.txt

test:
	@coverage run -m pytest -v ./tests

install:
	@~/.local/bin/pip install . --user --break-system-packages

publish:
	@python setup.py sdist bdist_wheel
	@twine upload dist/geniusrise-${GENIUSRISE_VERSION}-* --verbose
