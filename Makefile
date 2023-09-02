PYTHONPATH := $(PWD)/.
VENV := $(PWD)/.env

PATH := $(VENV)/bin:$(PATH)
BIN := PATH=$(PATH) PYTHONPATH=$(PYTHONPATH) $(VENV)/bin
py := $(BIN)/python3
pip := $(py) -m pip

.PHONY: bin
pythonpath:
	@echo $(BIN)

.PHONY: venv
venv:
	python3 -m venv $(VENV)
	$(pip) install --upgrade pip
	$(pip) install -r requirements.txt
