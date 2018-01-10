install:
	@pip install -U pip setuptools
	@pip install -U .

test: install
	@py.test circleci/test*py

inttest: install
	@py.test integration/test*py
