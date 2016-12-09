.PHONY: all
all: build
	$(info "There is no need to build anything!")

.PHONY: install
install:
	pip install --user -r requirements.txt

build: Dockerfile
	docker build -t seo/server .

.PHONY: tests
tests:
	$(info "Tests are not currently implemented")

.PHONY: clean
clean:
	rm -rf seo-capture/__pycache__
