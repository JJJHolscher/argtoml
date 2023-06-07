
pwd = $(shell pwd)
name = $(notdir $(pwd))

github_user_name = 

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
	ln -s "./src" "$(dirlink)"

share: $(venv) .git/refs/remotes/public
	git checkout main && \
	git push public
	#. .venv/bin/activate && \
	#python setup.py bump
	#git add pyproject.toml

test_publish: $(venv)
	if [ -d "./dist" ]; then rm -r "./dist" && mkdir "dist"; fi
	python -m build
	twine upload dist/* -r pypitest

publish: $(venv)
	[ -d "./dist" ] || rm -r "./dist" && mkdir "dist"
	python setup.py sdist bdist_wheel --universal
	twine upload dist/* -r pypitest

.git/refs/remotes/public:
	git checkout -b main
	$(eval user_name = $(shell yq ".authors.0.github" pyproject.toml))
	curl -u "$(user_name)" "https://api.github.com/user/repos" -d "{\"name\":\"$(name)\",\"private\":false}"
	git remote add github "https://github.com/$(user_name)/$(name)"
	git remote add public "/mnt/nas/git/$(name)"
	git remote set-url --add --push public "/mnt/nas/git/$(name)"
	git remote set-url --add --push public "https://github.com/$(user_name)/$(name)"
	git push public main

clean:
	rm -r .venv
	rm $(binlink)
	rm $(dirlink)

