.PHONY: run install

install:
	pip install -r requirements.txt

run:
	PYTHONPATH=. python  ./src/main.py