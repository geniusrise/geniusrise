##██ GENIUSRISE
# ██████████████████████████████████████████████████████████████████████

.DEFAULT_GOAL := help
SHELL := /bin/bash

setup: ## Install dependencies
	@pip install -r ./requirements.txt

developer-setup: ## Install development and testing dependencies
	@pip install -r ./requirements.txt
	@pip install -r ./requirements-dev.txt

test: ## Run tests (note: requires imports)
	@coverage run -m pytest -vv --log-cli-level=ERROR ./geniusrise/

install: ## Install using local system's pip
	@/usr/bin/pip install . --user --break-system-packages

publish: ## Publish to pypi
	@rm -rf dist build
	@python setup.py sdist bdist_wheel
	@twine upload dist/geniusrise-${GENIUSRISE_VERSION}-* --verbose

help: ## Dislay this help
	@echo ""
	@printf "\033[31m%-30s\033[0m %s\n" " ██████  ███████ ███    ██ ██ ██    ██ ███████ ██████  ██ ███████ ███████"
	@printf "\033[31m%-30s\033[0m %s\n" "██       ██      ████   ██ ██ ██    ██ ██      ██   ██ ██ ██      ██"
	@printf "\033[31m%-30s\033[0m %s\n" "██   ███ █████   ██ ██  ██ ██ ██    ██ ███████ ██████  ██ ███████ █████   "
	@printf "\033[31m%-30s\033[0m %s\n" "██    ██ ██      ██  ██ ██ ██ ██    ██      ██ ██   ██ ██      ██ ██"
	@printf "\033[31m%-30s\033[0m %s\n" " ██████  ███████ ██   ████ ██  ██████  ███████ ██   ██ ██ ███████ ███████"
	@echo ""
	@printf "\033[31m%-30s\033[0m %s\n" "🧠 https://geniusrise.ai"
	@echo ""

	@IFS=$$'\n'; for line in `grep -h -E '^[a-zA-Z_#-]+:?.*?## .*$$' $(MAKEFILE_LIST)`; do if [ "$${line:0:2}" = "##" ]; then \
	echo $$line | awk 'BEGIN {FS = "## "}; {printf "\n\033[33m%s\033[0m\n", $$2}'; else \
	echo $$line | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'; fi; \
	done; unset IFS;
