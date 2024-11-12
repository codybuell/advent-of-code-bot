VERSION=$(shell cat VERSION.md)

# set ALL targets to be PHONY
.PHONY: $(shell sed -n -e '/^$$/ { n ; /^[^ .\#][^ ]*:/ { s/:.*$$// ; p ; } ; }' $(MAKEFILE_LIST))

rpi4-container:
	DOCKER_BUILDKIT=1 docker build --platform linux/arm64 -t advent-of-code-bot:$(VERSION) .

rpi-cluster-deploy: rpi4-container
	docker tag advent-of-code-bot:$(VERSION) registry.buell.dev:5000/advent-of-code-bot:$(VERSION)
	docker push registry.buell.dev:5000/advent-of-code-bot:$(VERSION)
	kubectl create namespace advent-of-code-bot
	kubectl create secret generic advent-of-code-bot-secret \
		--namespace advent-of-code-bot \
		--from-literal='leaderboard_id=$(LEADERBOARD_ID)' \
		--from-literal='slack_webhook=$(SLACK_WEBHOOK)' \
		--from-literal='session_cookie=$(SESSION_ID)'
	kubectl apply -f advent-of-code-bot.yml

rpi-cluster-destroy:
	kubectl delete namespace advent-of-code-bot

rpi-cluster-logs:
	kubectl -n advent-of-code-bot logs -f deploy/advent-of-code-bot

clean:
	rm -f advent-of-code-bot-$(VERSION).tar
	rm -f members.json
