PREFIX ?= /usr/local
BINDIR ?= $(PREFIX)/bin
.DEFAULT_GOAL := test
.PHONY: test install uninstall

test:
	nosetests

install:
	install -m 755 deptool.py "$(BINDIR)/deptool"

uninstall:
	rm -f "$(BINDIR)/deptool"

