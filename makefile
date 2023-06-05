
pwd = $(shell pwd)
name = $(notdir $(pwd))

binlink = ${HOME}/.local/bin/$(name)
dirlink = $(pwd)/$(name)
venv = $(pwd)/.venv
venvbin = $(venv)/bin
activate = $(venv)/bin/activate

$(venv): $(venvbin) $(binlink) $(dirlink)
	touch $(venv)

$(venvbin): $(activate) requirements.txt
	. .venv/bin/activate && \
	pip install -r requirements.txt
	touch $(venvbin)

$(activate):
	python -m venv --prompt $(name) .venv
	. .venv/bin/activate && \
	pip install --upgrade pip;

$(binlink):
	echo "#!/bin/sh\n$(venv)/bin/python $(pwd)/src/main.py \"\$$@\"" > $(binlink)
	chmod +x $(binlink)

$(dirlink):
	sed "s/NAME/$(name)/" setup.py > setup.py.py
	mv setup.py.py setup.py
	ln -s "./src" "$(dirlink)"

clean:
	rm -r .venv
	rm $(binlink)
	rm $(dirlink)

