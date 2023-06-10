
pwd = $(shell pwd)
name = $(notdir $(pwd))
email = $(shell cat "$$HOME/.secret/email.txt")
version = $(shell yq ".project.version" pyproject.toml)

binlink = ${HOME}/.local/bin/$(name)
srclink = $(pwd)/$(name)
venv = $(pwd)/.venv
venvbin = $(venv)/bin
activate = $(venv)/bin/activate

define clear_dir
    if [ -d $(1) ]; then rm -r $(1); fi
    mkdir $(1)
endef

define increment_patch
    $(eval patch = $(shell echo $(version) | grep -o '[0-9]*$$'))
    $(eval patch = $(shell echo "$$(($(patch)+1))"))
    $(eval majorminor = $(shell echo $(version) | grep -o '^[0-9]*.[0-9]*.'))
    $(eval new_version = $(majorminor)$(patch))
    sed 's/version = .*/version = "$(new_version)"/' pyproject.toml > pyproject.temp
    mv pyproject.temp pyproject.toml
endef

define test_in_tmp
    $(call clear_dir,tmp)
    cd tmp && \
    python -m venv .venv
    . tmp/.venv/bin/activate && \
    pip install -i "$(1)" "$(name) == $(version)" || \
    pip install -i "$(1)" "$(name) == $(version)" && \
    python -m unittest "$(name).tests"
endef

$(venv): $(venvbin) $(binlink) $(srclink)
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

$(srclink):
	ln -s "./src" "$(srclink)"
	sed 's/NAME/$(name)/' pyproject.toml > pyproject.temp
	mv pyproject.temp pyproject.toml
	
share: $(venv) .git/refs/remotes/public
	git checkout main && \
	git push public main --tags

test_local: $(venv)
	python -m unittest src.tests

build:
	$(call clear_dir,dist)
	mv pyproject.toml pyproject.temp
	sed 's/^email = .*/email = "$(email)"/' pyproject.temp > pyproject.toml
	python -m build
	mv pyproject.temp pyproject.toml

test: $(venv) test_local build
	twine upload dist/* -r pypitest
	$(call increment_patch)
	$(call test_in_tmp,"https://test.pypi.org/simple")
	
publish: $(venv) build .git/refs/remotes/public
	git tag "v$(version)"
	git push public main --tags
	twine upload dist/*
	$(call increment_patch)
	$(call test_in_tmp,"https://pypi.org/simple")

.git/refs/remotes/public:
	git checkout -b main
	$(eval user_name = $(shell yq ".git.github" pyproject.toml))
	curl -u "$(user_name)" "https://api.github.com/user/repos" -d "{\"name\":\"$(name)\",\"private\":false}"
	git remote add github "https://github.com/$(user_name)/$(name)"
	git remote add public "/mnt/nas/git/$(name)"
	git remote set-url --add --push public "/mnt/nas/git/$(name)"
	git remote set-url --add --push public "https://github.com/$(user_name)/$(name)"

clean:
	rm -r .venv
	rm $(binlink)
	rm $(srclink)

