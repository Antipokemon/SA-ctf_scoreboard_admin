.PHONY: test package clean

test:
	python3 -m unittest discover -s tests -v
	python3 -m py_compile overrides/bin/*.py scripts/*.py

package: test
	./scripts/build.sh

clean:
	rm -rf build dist
