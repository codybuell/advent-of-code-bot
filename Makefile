VERSION=$(shell cat VERSION.md)

rpi4-container:
	DOCKER_BUILDKIT=1 docker build --platform linux/arm64 -t advent-of-code-bot:$(VERSION) .
	docker save --output advent-of-code-bot-$(VERSION).tar advent-of-code-bot:$(VERSION)
