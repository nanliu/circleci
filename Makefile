ACTIVATE := .venv/bin/activate

install:
	@test -d .venv || virtualenv .venv
	@. $(ACTIVATE); pip install -U pip setuptools
	@pip install -U .

test: install
	@. $(ACTIVATE); py.test circleci/test*py

inttest: install
	@. $(ACTIVATE); py.test integration/test*py
