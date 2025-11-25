.PHONY: $(VERSIONS) build-% test-% test-all

VERSIONS = 3.10 3.11 3.12 3.13 3.14


build-%:
	docker build --build-arg PYTHON_VERSION=$* \
		-t pico_stack-test:$* --no-cache -f Dockerfile.test .

test-%: build-%
	docker run --rm pico_stack-test:$*

test-all: $(addprefix test-, $(VERSIONS))
	@echo "✅ All versions done"

