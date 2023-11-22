VERSION=$(shell cat VERSION.md)

# set ALL targets to be PHONY
.PHONY: $(shell sed -n -e '/^$$/ { n ; /^[^ .\#][^ ]*:/ { s/:.*$$// ; p ; } ; }' $(MAKEFILE_LIST))

rpi4-container:
	DOCKER_BUILDKIT=1 docker build --platform linux/arm64 -t advent-of-code-bot:$(VERSION) .
	docker save --output advent-of-code-bot-$(VERSION).tar advent-of-code-bot:$(VERSION)

rpi-cluster-deploy: rpi4-container
	scp advent-of-code-bot-$(VERSION).tar k3s-a:~/
	scp advent-of-code-bot-$(VERSION).tar k3s-b:~/
	scp advent-of-code-bot-$(VERSION).tar k3s-c:~/
	scp advent-of-code-bot-$(VERSION).tar k3s-d:~/
	scp advent-of-code-bot-$(VERSION).tar k3s-e:~/
	ssh k3s-a "sudo k3s ctr images import ./advent-of-code-bot-$(VERSION).tar"
	ssh k3s-b "sudo k3s ctr images import ./advent-of-code-bot-$(VERSION).tar"
	ssh k3s-c "sudo k3s ctr images import ./advent-of-code-bot-$(VERSION).tar"
	ssh k3s-d "sudo k3s ctr images import ./advent-of-code-bot-$(VERSION).tar"
	ssh k3s-e "sudo k3s ctr images import ./advent-of-code-bot-$(VERSION).tar"
	kubectl create namespace advent-of-code-bot
	kubectl create secret generic advent-of-code-bot-secret \
		--namespace advent-of-code-bot \
		--from-literal='leaderboard_id=$(LEADERBOARD_ID)' \
		--from-literal='slack_webhook=$(SLACK_WEBHOOK)' \
		--from-literal='session_cookie=$(SESSION_ID)'
	kubectl apply -f advent-of-code-bot.yml

rpi-cluster-destroy:
	ssh k3s-a "rm -f ~/advent-of-code-bot-$(VERSION).tar"
	ssh k3s-b "rm -f ~/advent-of-code-bot-$(VERSION).tar"
	ssh k3s-c "rm -f ~/advent-of-code-bot-$(VERSION).tar"
	ssh k3s-d "rm -f ~/advent-of-code-bot-$(VERSION).tar"
	ssh k3s-e "rm -f ~/advent-of-code-bot-$(VERSION).tar"
	ssh k3s-a "sudo k3s ctr images rm docker.io/library/advent-of-code-bot:$(VERSION)"
	ssh k3s-b "sudo k3s ctr images rm docker.io/library/advent-of-code-bot:$(VERSION)"
	ssh k3s-c "sudo k3s ctr images rm docker.io/library/advent-of-code-bot:$(VERSION)"
	ssh k3s-d "sudo k3s ctr images rm docker.io/library/advent-of-code-bot:$(VERSION)"
	ssh k3s-e "sudo k3s ctr images rm docker.io/library/advent-of-code-bot:$(VERSION)"
	kubectl delete namespace advent-of-code-bot

rpi-cluster-logs:
	kubectl -n advent-of-code-bot logs -f deploy/advent-of-code-bot

clean:
	rm -f advent-of-code-bot-$(VERSION).tar
	rm -f members.json
