
install:
	@virtualenv venv
	@source venv/bin/activate && pip install -r ./requirements.txt

developer-install:
	@pip install -r ./requirements.txt
	@pip install -r ./requirements-dev.txt

test:
	@coverage run -m pytest -v ./test
