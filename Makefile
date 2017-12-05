.PHONY: all clean

all: charm-proof

clean:
	rm -rf .venv

.venv:
	virtualenv .venv

.venv/bin/charm-proof: .venv
	.venv/bin/pip install simplejson charm-tools

charm-proof: .venv/bin/charm-proof
	.venv/bin/charm-proof