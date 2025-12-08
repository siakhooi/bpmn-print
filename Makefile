help:
clean:
	rm -rf dist target coverage \
	src/bpmn_print/__pycache__ \
	tests/__pycache__
run:
	poetry run bpmn-print /home/sing/.mygh/bpmn-pretty-print/intent_based_digital_content/service_specs/processes /tmp/bpmn_output
set-version:
	scripts/set-version.sh
build:
	poetry build
install:
	poetry install
flake8:
	poetry run flake8
update:
	poetry update
test:
	 poetry run pytest --capture=sys \
	 --junit-xml=coverage/test-results.xml \
	 --cov=bpmn_print \
	 --cov-report term-missing  \
	 --cov-report xml:coverage/coverage.xml \
	 --cov-report html:coverage/coverage.html \
	 --cov-report lcov:coverage/coverage.info -vv

all: clean set-version install flake8 build test

release:
	scripts/release.sh

commit:
	scripts/git-commit.sh
	git push


# system-deps:
# 	sudo apt-get update && sudo apt-get install -y libcairo2-dev pkg-config python3-dev graphviz

#svglib pillow bpmn-python


