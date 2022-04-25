SHELL := /bin/bash -O extglob

.PHONY: all forms zip clean format check prebuild install

all: zip

zip:
	python -m ankibuild --type package --install --qt all --noconsts --forms-dir forms --install

ankiweb:
	python -m ankibuild --type ankiweb --install --qt all --noconsts --forms-dir forms --install

run: zip
	python -m ankirun

format:
	python -m black src/

check:
	python -m mypy .

clean:
	rm -f $(PACKAGE_NAME).ankiaddon
