#
#  Standard Makefile supports targets build, install and clean + static
#  code checking. make install respects DESTDIR, build and install respects
#  V=0 and V=1
PYLINT          = pylint-3

ifeq ($(DESTDIR),)
    DESTDIR     = $(CURDIR)/install
endif

VERBOSE         = $(or $(V),0)
ifeq ($(VERBOSE), 0)
    QUIET_OPT   = --quiet
endif

PYTHON_SRC      = plugins lib/ddupdate setup.py ddupdate ddupdate-config

# vim-compatible error reporting:
pylint_template = {path}:{line}: [{msg_id}({symbol}), {obj}] {msg}


all:	build

build:
	python3 setup.py $(QUIET_OPT) build

install: .phony
	python3 setup.py $(QUIET_OPT) install --root=$(DESTDIR)

clean: .phony
	python3 setup.py clean

pylint: $(PYTHON_SRC)
	-PYTHONPATH=$(CURDIR)/lib $(PYLINT) \
	        --rcfile=pylint.conf \
	        --msg-template='$(pylint_template)' \
	        $?

pydocstyle: $(PYTHON_SRC)
	pydocstyle $?

pycodestyle: $(PYTHON_SRC)
	-pycodestyle $?

.phony:
