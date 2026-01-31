# Makefile for ansible-doc-template-extractor project
#
# Use this to get information on the targets:
#   make  - or -  make help
#
# It is recommended to run this Makefile in a virtual Python environment,
# because Python packages will be installed automatically.
#
# Supported OS platforms:
#     Windows (native)
#     Linux (any)
#     macOS/OS-X
#
# OS-level commands used by this Makefile (to be provided manually):
#   On native Windows:
#     cmd (providing: del, copy, rmdir, set)
#     where
#   On Linux and macOS:
#     rm, find, cp, env, sort, which, uname
#
# Environment variables:
#   PYTHON_CMD: Python command to use (OS-X needs to distinguish Python 2/3)
#   PIP_CMD: Pip command to use (OS-X needs to distinguish Python 2/3)

# No built-in rules needed:
MAKEFLAGS += --no-builtin-rules
.SUFFIXES:

# Python / Pip commands
ifndef PYTHON_CMD
  PYTHON_CMD := python
endif
ifndef PIP_CMD
  PIP_CMD := pip
endif

# Run type (normal, scheduled, release, local)
ifndef RUN_TYPE
  RUN_TYPE := local
endif

# Determine OS platform make runs on.
ifeq ($(OS),Windows_NT)
  ifdef PWD
    PLATFORM := Windows_UNIX
  else
    PLATFORM := Windows_native
    ifndef COMSPEC
      # Make variables are case sensitive and some native Windows environments have
      # ComSpec set instead of COMSPEC.
      ifdef ComSpec
        COMSPEC = $(ComSpec)
      endif
    endif
    ifdef COMSPEC
      SHELL := $(subst \,/,$(COMSPEC))
    else
      SHELL := cmd.exe
    endif
    .SHELLFLAGS := /c
  endif
else
  # Values: Linux, Darwin
  PLATFORM := $(shell uname -s)
endif

ifeq ($(PLATFORM),Windows_native)
  # Note: The substituted backslashes must be doubled.
  # Remove files (blank-separated list of wildcard path specs)
  RM_FUNC = del /f /q $(subst /,\\,$(1))
  # Remove files recursively (single wildcard path spec)
  RM_R_FUNC = del /f /q /s $(subst /,\\,$(1))
  # Remove directories (blank-separated list of wildcard path specs)
  RMDIR_FUNC = rmdir /q /s $(subst /,\\,$(1))
  # Remove directories recursively (single wildcard path spec)
  RMDIR_R_FUNC = rmdir /q /s $(subst /,\\,$(1))
  # Copy a file, preserving the modified date
  CP_FUNC = copy /y $(subst /,\\,$(1)) $(subst /,\\,$(2))
  ENV = set
  WHICH = where
else
  RM_FUNC = rm -f $(1)
  RM_R_FUNC = find . -type f -name '$(1)' -delete
  RMDIR_FUNC = rm -rf $(1)
  RMDIR_R_FUNC = find . -type d -name '$(1)' | xargs -n 1 rm -rf
  CP_FUNC = cp -r $(1) $(2)
  ENV = env | sort
  WHICH = which -a
endif

# Pypi package name
pypi_package_name := ansible-doc-template-extractor

# Python package name (also used for dist archive names)
python_package_name := ansible_doc_template_extractor

# Package directory
package_dir := src/ansible_doc_template_extractor

# Package version (e.g. "1.0.0a1.dev10+gd013028e" during development, or "1.0.0"
# when releasing).
# Note: The package version is automatically calculated by setuptools_scm based
# on the most recent tag in the commit history, increasing the least significant
# version indicator by 1.
package_version := $(shell $(PYTHON_CMD) -m setuptools_scm)

# Docker image
docker_image_name := ansible-doc-template-extractor
docker_image_tag := latest

python_mn_version := $(shell $(PYTHON_CMD) -c "import sys; sys.stdout.write('{}.{}'.format(sys.version_info[0], sys.version_info[1]))")
pymn := $(shell $(PYTHON_CMD) -c "import sys; sys.stdout.write('py{}{}'.format(sys.version_info[0], sys.version_info[1]))")

# The version file is recreated by setuptools-scm on every build, so it is
# excluded from git, and also from some dependency lists.
version_file := $(package_dir)/_version_scm.py

# Source files in the package, including $(version_file) if created
package_py_files := \
    $(wildcard $(package_dir)/*.py) \
    $(wildcard $(package_dir)/*/*.py) \

# Source files in the package, excluding $(version_file)
package_py_files_no_version := \
    $(filter-out $(version_file), $(package_py_files))

dist_dir := dist
bdist_file := $(dist_dir)/$(python_package_name)-$(package_version)-py3-none-any.whl
sdist_file := $(dist_dir)/$(python_package_name)-$(package_version).tar.gz

# Dependencies of the distribution archives. Since the $(version_file) is
# created when building the distribution archives, this must not contain
# the $(version_file).
dist_dependent_files := \
    pyproject.toml \
    LICENSE \
    README.md \
    requirements.txt \
    $(package_py_files_no_version) \
    $(wildcard $(package_dir)/templates/*.j2) \
    $(wildcard $(package_dir)/schemas/*.yml) \

# Example files
example_role_dirs := $(wildcard examples/roles/*)
example_role_md_files := $(patsubst examples/roles/%,examples/output/%.md,$(example_role_dirs))
example_role_rst_files := $(patsubst examples/roles/%,examples/output/%.rst,$(example_role_dirs))
example_playbook_files := $(wildcard examples/playbooks/*)
example_playbook_md_files := $(patsubst examples/playbooks/%.meta.yml,examples/output/%.md,$(example_playbook_files))
example_playbook_rst_files := $(patsubst examples/playbooks/%.meta.yml,examples/output/%.rst,$(example_playbook_files))

# Directory for .done files
done_dir := done

# Bandit config file
bandit_rc_file := .bandit.toml

# Flake8 config file
flake8_rc_file := .flake8

# Ruff config file
ruff_rc_file := .ruff.toml

# PyLint config file
pylint_rc_file := .pylintrc

pip_level_opts := --upgrade --upgrade-strategy eager

# Pytest
test_dir := tests

test_py_files := \
    $(wildcard $(test_dir)/*.py) \
		$(wildcard $(test_dir)/*/*.py) \

pytest_base_opts := $(TESTOPTS)
ifdef TESTCASES
  pytest_opts := $(pytest_base_opts) -k "$(TESTCASES)"
else
  pytest_opts := $(pytest_base_opts)
endif

.PHONY: help
help:
	@echo "Makefile for project $(pypi_package_name)"
	@echo "Package version: $(package_version)"
	@echo "Python version: $(python_mn_version)"
	@echo "Targets:"
	@echo "  install    - Install package and its prerequisites (non-editable)"
	@echo "  develop    - Install prerequisites for development"
	@echo "  check      - Perform flake8 checks"
	@echo "  ruff       - Perform ruff checks (an alternate lint tool)"
	@echo "  pylint     - Perform pylint checks"
	@echo "  bandit     - Run bandit checker"
	@echo "  build      - Build the distribution files in $(dist_dir)"
	@echo "  test       - Run unit and function tests"
	@echo "  authors    - Generate AUTHORS.md file from git log"
	@echo "  examples   - Generate the examples"
	@echo "  all        - Do all of the above"
	@echo "  release_branch - Create a release branch when releasing a version (requires VERSION and optionally BRANCH to be set)"
	@echo "  release_publish - Publish to PyPI when releasing a version (requires VERSION and optionally BRANCH to be set)"
	@echo "  start_branch - Create a start branch when starting a new version (requires VERSION and optionally BRANCH to be set)"
	@echo "  start_tag - Create a start tag when starting a new version (requires VERSION and optionally BRANCH to be set)"
	@echo "  clean      - Remove any temporary files"
	@echo "  clobber    - Remove any build products"
	@echo "  platform   - Display the information about the platform as seen by make"
	@echo "  env        - Display the environment as seen by make"
	@echo "Environment variables:"
	@echo "  PYTHON_CMD=... - Name of python command. Default: python"
	@echo "  PIP_CMD=... - Name of pip command. Default: pip"
	@echo "  VERSION=... - M.N.U version to be released or started"
	@echo "  BRANCH=... - Name of branch to be released or started (default is derived from VERSION)"

.PHONY: platform
platform:
ifeq ($(PLATFORM),Linux)
	@echo "Makefile: Installing ld to get Linux distributions"
	$(PYTHON_CMD) -m pip -q install ld
endif
	@echo "Makefile: Platform information as seen by make:"
	@echo "Platform detected by Makefile: $(PLATFORM)"
	@$(PYTHON_CMD) -c "import platform; print(f'Platform detected by Python: {platform.platform()}')"
	@$(PYTHON_CMD) -c "import platform; print(f'HW platform detected by Python: {platform.machine()}')"
ifeq ($(PLATFORM),Linux)
	@$(PYTHON_CMD) -c "import ld; d=ld.linux_distribution(); print(f'Linux distro detected by ld: {d[0]} {d[1]}')"
endif
	@echo "Shell used for commands: $(SHELL)"
	@echo "Shell flags: $(.SHELLFLAGS)"
	@echo "Make version: $(MAKE_VERSION)"
	@echo "Python command name: $(PYTHON_CMD)"
	@echo "Python command location: $(shell $(WHICH) $(PYTHON_CMD))"
	@echo "Python version: $(python_mn_version)"
	@echo "Pip command name: $(PIP_CMD)"
	@echo "Pip command location: $(shell $(WHICH) $(PIP_CMD))"
	@echo "Pip version: $(shell $(PIP_CMD) --version)"
	@echo "$(pypi_package_name) package version: $(package_version)"

.PHONY: env
env:
	@echo "Makefile: Environment variables as seen by make:"
	$(ENV)

.PHONY: _check_version
_check_version:
ifeq (,$(package_version))
	$(error Package version could not be determined)
endif

.PHONY: _always
_always:

.PHONY: install
install: $(done_dir)/install_$(pymn).done
	@echo "Makefile: $@ done."

.PHONY: develop
develop: $(done_dir)/develop_$(pymn).done
	@echo "Makefile: $@ done."

.PHONY: check
check: $(done_dir)/flake8_$(pymn).done
	@echo "Makefile: $@ done."

.PHONY: ruff
ruff: $(done_dir)/ruff_$(pymn).done
	@echo "Makefile: $@ done."

.PHONY: pylint
pylint: $(done_dir)/pylint_$(pymn).done
	@echo "Makefile: $@ done."

.PHONY: bandit
bandit: $(done_dir)/bandit_$(pymn).done
	@echo "Makefile: $@ done."

.PHONY: build
build: _check_version $(bdist_file) $(sdist_file)
	@echo "Makefile: $@ done."

.PHONY: all
all: install develop check ruff pylint bandit build test authors
	@echo "Makefile: $@ done."

.PHONY: examples
examples: $(example_role_md_files) $(example_role_rst_files) $(example_playbook_md_files) $(example_playbook_rst_files)
	@echo "Makefile: $@ done."

examples/output/%.md: examples/roles/%/meta/argument_specs.yml $(package_dir)/templates/role.md.j2 $(done_dir)/install_$(pymn).done
	ansible-doc-template-extractor -v --format md --out-dir examples/output $<

examples/output/%.rst: examples/roles/%/meta/argument_specs.yml $(package_dir)/templates/role.rst.j2 $(done_dir)/install_$(pymn).done
	ansible-doc-template-extractor -v --format rst --out-dir examples/output $<

examples/output/%.md: examples/playbooks/%.meta.yml $(package_dir)/templates/playbook.md.j2 $(done_dir)/install_$(pymn).done
	ansible-doc-template-extractor -v --format md --out-dir examples/output $<

examples/output/%.rst: examples/playbooks/%.meta.yml $(package_dir)/templates/playbook.rst.j2 $(done_dir)/install_$(pymn).done
	ansible-doc-template-extractor -v --format rst --out-dir examples/output $<

.PHONY: release_branch
release_branch:
	@bash -c 'if [ -z "$(VERSION)" ]; then echo ""; echo "Error: VERSION env var is not set"; echo ""; false; fi'
	@bash -c 'if [ -n "$$(git status -s)" ]; then echo ""; echo "Error: Local git repo has uncommitted files:"; echo ""; git status; false; fi'
	git fetch origin
	@bash -c 'if [ -z "$$(git tag -l $(VERSION)a0)" ]; then echo ""; echo "Error: Release start tag $(VERSION)a0 does not exist (the version has not been started)"; echo ""; false; fi'
	@bash -c 'if [ -n "$$(git tag -l $(VERSION))" ]; then echo ""; echo "Error: Release tag $(VERSION) already exists (the version has already been released)"; echo ""; false; fi'
	@bash -c 'if [[ -n "$${BRANCH}" ]]; then echo $${BRANCH} >branch.tmp; elif [[ "$${VERSION#*.*.}" == "0" ]]; then echo "main" >branch.tmp; else echo "stable_$${VERSION%.*}" >branch.tmp; fi'
	@bash -c 'if [ -z "$$(git branch --contains $(VERSION)a0 $$(cat branch.tmp))" ]; then echo ""; echo "Error: Release start tag $(VERSION)a0 is not in target branch $$(cat branch.tmp), but in:"; echo ""; git branch --contains $(VERSION)a0;. false; fi'
	@echo "==> This will start the release of $(pypi_package_name) version $(VERSION) to PyPI using target branch $$(cat branch.tmp)"
	@echo -n '==> Continue? [yN] '
	@bash -c 'read answer; if [ "$$answer" != "y" ]; then echo "Aborted."; false; fi'
	bash -c 'git checkout $$(cat branch.tmp)'
	git pull
	@bash -c 'if [ -z "$$(git branch -l release_$(VERSION))" ]; then echo "Creating release branch release_$(VERSION)"; git checkout -b release_$(VERSION); fi'
	git checkout release_$(VERSION)
	make authors
	echo "Dummy change for releasing version $(VERSION)" >done/.dummy
	git add done/.dummy
	git commit -asm "Release $(VERSION)"
	git push --set-upstream origin release_$(VERSION)
	rm -f branch.tmp
	@echo "Done: Pushed the release branch to GitHub - now go there and create a PR."
	@echo "Makefile: $@ done."

.PHONY: release_publish
release_publish:
	@bash -c 'if [ -z "$(VERSION)" ]; then echo ""; echo "Error: VERSION env var is not set"; echo ""; false; fi'
	@bash -c 'if [ -n "$$(git status -s)" ]; then echo ""; echo "Error: Local git repo has uncommitted files:"; echo ""; git status; false; fi'
	git fetch origin
	@bash -c 'if [ -n "$$(git tag -l $(VERSION))" ]; then echo ""; echo "Error: Release tag $(VERSION) already exists (the version has already been released)"; echo ""; false; fi'
	@bash -c 'if [[ -n "$${BRANCH}" ]]; then echo $${BRANCH} >branch.tmp; elif [[ "$${VERSION#*.*.}" == "0" ]]; then echo "main" >branch.tmp; else echo "stable_$${VERSION%.*}" >branch.tmp; fi'
	@bash -c 'if ! git show-ref --quiet refs/remotes/origin/$$(cat branch.tmp); then echo ""; echo "Error: Branch origin/$$(cat branch.tmp) does not exist. Incorrect VERSION env var?"; echo ""; false; fi'
	@bash -c 'if [[ ! $$(git log --format=format:%s origin/$$(cat branch.tmp)~..origin/$$(cat branch.tmp)) =~ ^Release\ $(VERSION) ]]; then echo ""; echo "Error: Release PR for $(VERSION) has not been merged yet"; echo ""; false; fi'
	@echo "==> This will publish $(pypi_package_name) version $(VERSION) to PyPI using target branch $$(cat branch.tmp)"
	@echo -n '==> Continue? [yN] '
	@bash -c 'read answer; if [ "$$answer" != "y" ]; then echo "Aborted."; false; fi'
	bash -c 'git checkout $$(cat branch.tmp)'
	git pull
	git tag -f $(VERSION)
	git push -f --tags
	-git branch -D release_$(VERSION)
	-git branch -D -r origin/release_$(VERSION)
	rm -f branch.tmp
	@echo "Done: Triggered the publish workflow - now wait for it to finish and verify the publishing."
	@echo "Makefile: $@ done."

.PHONY: start_branch
start_branch:
	@bash -c 'if [ -z "$(VERSION)" ]; then echo ""; echo "Error: VERSION env var is not set"; echo ""; false; fi'
	@bash -c 'if [ -n "$$(git status -s)" ]; then echo ""; echo "Error: Local git repo has uncommitted files:"; echo ""; git status; false; fi'
	git fetch origin
	@bash -c 'if [ -n "$$(git tag -l $(VERSION))" ]; then echo ""; echo "Error: Release tag $(VERSION) already exists (the version has already been released)"; echo ""; false; fi'
	@bash -c 'if [ -n "$$(git tag -l $(VERSION)a0)" ]; then echo ""; echo "Error: Release start tag $(VERSION)a0 already exists (the new version has alreay been started)"; echo ""; false; fi'
	@bash -c 'if [ -n "$$(git branch -l start_$(VERSION))" ]; then echo ""; echo "Error: Start branch start_$(VERSION) already exists (the start of the new version is already underway)"; echo ""; false; fi'
	@bash -c 'if [[ -n "$${BRANCH}" ]]; then echo $${BRANCH} >branch.tmp; elif [[ "$${VERSION#*.*.}" == "0" ]]; then echo "main" >branch.tmp; else echo "stable_$${VERSION%.*}" >branch.tmp; fi'
	@echo "==> This will start new version $(VERSION) using target branch $$(cat branch.tmp)"
	@echo -n '==> Continue? [yN] '
	@bash -c 'read answer; if [ "$$answer" != "y" ]; then echo "Aborted."; false; fi'
	bash -c 'git checkout $$(cat branch.tmp)'
	git pull
	git checkout -b start_$(VERSION)
	echo "Dummy change for starting version $(VERSION)" >done/.dummy
	git add done/.dummy
	git commit -asm "Start $(VERSION)"
	git push --set-upstream origin start_$(VERSION)
	rm -f branch.tmp
	@echo "Done: Pushed the start branch to GitHub - now go there and create a PR."
	@echo "Makefile: $@ done."

.PHONY: start_tag
start_tag:
	@bash -c 'if [ -z "$(VERSION)" ]; then echo ""; echo "Error: VERSION env var is not set"; echo ""; false; fi'
	@bash -c 'if [ -n "$$(git status -s)" ]; then echo ""; echo "Error: Local git repo has uncommitted files:"; echo ""; git status; false; fi'
	git fetch origin
	@bash -c 'if [ -n "$$(git tag -l $(VERSION)a0)" ]; then echo ""; echo "Error: Release start tag $(VERSION)a0 already exists (the new version has alreay been started)"; echo ""; false; fi'
	@bash -c 'if [[ -n "$${BRANCH}" ]]; then echo $${BRANCH} >branch.tmp; elif [[ "$${VERSION#*.*.}" == "0" ]]; then echo "main" >branch.tmp; else echo "stable_$${VERSION%.*}" >branch.tmp; fi'
	@bash -c 'if ! git show-ref --quiet refs/remotes/origin/$$(cat branch.tmp); then echo ""; echo "Error: Branch origin/$$(cat branch.tmp) does not exist. Incorrect VERSION env var?"; echo ""; false; fi'
	@bash -c 'if [[ ! $$(git log --format=format:%s origin/$$(cat branch.tmp)~..origin/$$(cat branch.tmp)) =~ ^Start\ $(VERSION) ]]; then echo ""; echo "Error: Start PR for $(VERSION) has not been merged yet"; echo ""; false; fi'
	@echo "==> This will complete the start of new version $(VERSION) using target branch $$(cat branch.tmp)"
	@echo -n '==> Continue? [yN] '
	@bash -c 'read answer; if [ "$$answer" != "y" ]; then echo "Aborted."; false; fi'
	bash -c 'git checkout $$(cat branch.tmp)'
	git pull
	git tag -f $(VERSION)a0
	git push -f --tags
	-git branch -D start_$(VERSION)
	-git branch -D -r origin/start_$(VERSION)
	rm -f branch.tmp
	@echo "Done: Pushed the release start tag and cleaned up the release start branch."
	@echo "Makefile: $@ done."

.PHONY: authors
authors: AUTHORS.md
	@echo "Makefile: $@ done."

# Make sure the AUTHORS.md file is up to date but has the old date when it did
# not change to prevent redoing dependent targets.
AUTHORS.md: _always
	echo "# Authors of this project" >AUTHORS.md.tmp
	echo "" >>AUTHORS.md.tmp
	echo "Sorted list of authors derived from git commit history:" >>AUTHORS.md.tmp
	echo '```' >>AUTHORS.md.tmp
	bash -c "git shortlog --summary --email HEAD | cut -f 2 | LC_ALL=C.UTF-8 sort >>AUTHORS.md.tmp"
	echo '```' >>AUTHORS.md.tmp
	bash -c "if ! diff -q AUTHORS.md.tmp AUTHORS.md; then echo 'Updating AUTHORS.md as follows:'; diff AUTHORS.md.tmp AUTHORS.md; mv AUTHORS.md.tmp AUTHORS.md; else echo 'AUTHORS.md was already up to date'; rm AUTHORS.md.tmp; fi"

.PHONY: clean
clean:
	-$(call RM_R_FUNC,*.pyc)
	-$(call RM_R_FUNC,*.tmp)
	-$(call RM_R_FUNC,tmp_*)
	-$(call RM_FUNC,MANIFEST MANIFEST.in)
	-$(call RMDIR_R_FUNC,__pycache__)
	-$(call RMDIR_FUNC,build src/ansible_doc_template_extractor.egg-info .pytest_cache .coverage.*)
	@echo "Makefile: $@ done."

.PHONY: clobber
clobber: clean
	-$(call RMDIR_FUNC,$(doc_build_dir) htmlcov .coverage)
	-$(call RM_R_FUNC,*.done)
	@echo "Makefile: $@ done."

$(done_dir)/base_$(pymn).done: requirements-base.txt
	@echo "Makefile: Installing base packages"
	-$(call RM_FUNC,$@)
	$(PYTHON_CMD) -m pip install $(pip_level_opts) -r requirements-base.txt
	@echo "Makefile: Done installing base packages"
	echo "done" >$@

$(done_dir)/install_$(pymn).done: $(done_dir)/base_$(pymn).done requirements.txt $(dist_dependent_files)
	@echo "Makefile: Installing package (non-editable) and its prerequisites"
	-$(call RM_FUNC,$@)
	$(PYTHON_CMD) -m pip install $(pip_level_opts) .
	@echo "Makefile: Done installing package and its prerequisites"
	echo "done" >$@

$(done_dir)/develop_$(pymn).done: $(done_dir)/install_$(pymn).done requirements-develop.txt
	@echo "Makefile: Installing prerequisites for development"
	-$(call RM_FUNC,$@)
	$(PYTHON_CMD) -m pip install $(pip_level_opts) -r requirements-develop.txt
	@echo "Makefile: Done installing prerequisites for development"
	echo "done" >$@

$(sdist_file): $(done_dir)/develop_$(pymn).done $(dist_dependent_files)
	@echo "Makefile: Building the source distribution archive: $(sdist_file)"
	$(PYTHON_CMD) -m build --no-isolation --sdist --outdir $(dist_dir) .
	bash -c "ls -l $(sdist_file) || ls -l $(dist_dir) && $(PYTHON_CMD) -m setuptools_scm"
	@echo "Makefile: Done building the source distribution archive: $(sdist_file)"

$(bdist_file) $(version_file): $(done_dir)/develop_$(pymn).done $(dist_dependent_files)
	@echo "Makefile: Building the wheel distribution archive: $(bdist_file)"
	$(PYTHON_CMD) -m build --no-isolation --wheel --outdir $(dist_dir) -C--universal .
	bash -c "ls -l $(bdist_file) $(version_file) || ls -l $(dist_dir) && $(PYTHON_CMD) -m setuptools_scm"
	@echo "Makefile: Done building the wheel distribution archive: $(bdist_file)"

$(done_dir)/flake8_$(pymn).done: $(done_dir)/develop_$(pymn).done $(flake8_rc_file) $(package_py_files_no_version) $(test_py_files)
	@echo "Makefile: Performing flake8 checks"
	flake8 --config $(flake8_rc_file) $(package_py_files_no_version) $(test_dir)
	echo "done" >$@
	@echo "Makefile: Done performing flake8 checks"

$(done_dir)/ruff_$(pymn).done: $(done_dir)/develop_$(pymn).done $(ruff_rc_file) $(package_py_files_no_version) $(test_py_files)
	@echo "Makefile: Performing ruff checks"
	-$(call RM_FUNC,$@)
	ruff check --unsafe-fixes --config $(ruff_rc_file) $(package_py_files_no_version) $(test_dir)
	echo "done" >$@
	@echo "Makefile: Done performing ruff checks"

$(done_dir)/pylint_$(pymn).done: $(done_dir)/develop_$(pymn).done $(pylint_rc_file) $(package_py_files_no_version) $(test_py_files)
	@echo "Makefile: Performing pylint checks"
	pylint --rcfile=$(pylint_rc_file) --disable=fixme $(package_py_files_no_version) $(test_dir)
	echo "done" >$@
	@echo "Makefile: Done performing pylint checks"

$(done_dir)/bandit_$(pymn).done: $(done_dir)/develop_$(pymn).done $(bandit_rc_file) $(package_py_files_no_version)
	@echo "Makefile: Running Bandit"
	-$(call RM_FUNC,$@)
	bandit -c $(bandit_rc_file) -l $(package_py_files_no_version) $(test_dir)
	echo "done" >$@
	@echo "Makefile: Done running Bandit"

.PHONY: test
test: $(done_dir)/develop_$(pymn).done
	bash -c "PYTHONPATH=src coverage run --append --source=$(package_dir) -m pytest $(pytest_opts) $(test_dir)"
	coverage report
	@echo "Makefile: Done running unit and function tests"
