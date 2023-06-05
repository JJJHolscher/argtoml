
pwd = $(shell pwd)
name = $(notdir $(pwd))
symlink = ${HOME}/.local/bin/$(name)
venv = $(pwd)/.venv/bin/python

$(symlink): $(venv)
	echo "#!/bin/sh\n$(venv) $(pwd)/src/main.py \"\$$@\"" > $(symlink)
	chmod +x $(symlink)

$(venv): requirements.txt
	python -m venv --prompt $(name) .venv
	. .venv/bin/activate; \
	pip install --upgrade pip; \
	pip install -r requirements.txt

clean:
	rm -r .venv
	rm $(symlink)

