.PHONY: help prepare test lint run doc clean

VENV_PATH=.venv
PYTHON=${VENV_PATH}/bin/python3
PYTEST=${VENV_PATH}/bin/py.test

.DEFAULT: help
help:
	@echo "make prepare"
	@echo "       prepare development environment, use only once"
	@echo "make clean"
	@echo "       destroys the development environment"
	@echo "make test"
	@echo "       run tests"
	@echo "make lint"
	@echo "       run pylint and mypy"
	@echo "make run"
	@echo "       run project"
	@echo "make package"
	@echo "       build python package"
	@echo "make docker"
	@echo "       build docker image"

${VENV_PATH}/bin/activate:
	test -d ${VENV_PATH} || python3 -m venv ${VENV_PATH}
	${PYTHON} -m pip install -r requirements-dev.txt
	${PYTHON} -m pip install -e .
	touch ${VENV_PATH}/bin/activate

venv: ${VENV_PATH}/bin/activate
	. ${VENV_PATH}/bin/activate

prepare: venv

lint: venv
	${PYTHON} -m pylint dummyserver

test: venv
	${PYTEST} tests

run: venv
	${PYTHON} dummyserver

package: venv
	${PYTHON} setup.py sdist

docker:
	docker build -t eurotech/dummyserver .

clean:
	rm -rf ${VENV_PATH}
