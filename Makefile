#
#  Standard Makefile supports targets build, install and clean + static
#  code checking. make install respects DESTDIR.


ifeq ($(DESTDIR),)
    DESTDIR     = $(CURDIR)/install
endif

PYTHON_SRC      = plugins lib/ddupdate setup.py ddupdate ddupdate-config

# vim-compatible error reporting:
pylint_template = {path}:{line}: [{msg_id}({symbol}), {obj}] {msg}


all:	build

build:
	python3 setup.py --quiet build

install: .phony
	python3 setup.py --quiet install --root=$(DESTDIR)

clean: .phony
	python3 setup.py clean

pylint: $(PYTHON_SRC)
	-PYTHONPATH=$(CURDIR)/lib python3-pylint \
	        --rcfile=pylint.conf \
	        --msg-template='$(pylint_template)' \
	        $?

pydocstyle: $(PYTHON_SRC)
	pydocstyle $?

pycodestyle: $(PYTHON_SRC)
	pycodestyle $?

.phony:
