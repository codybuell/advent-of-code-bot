Advent-of-Code Bot
==================

A Slack bot for [Advent of Code](https://adventofcode.com). Adapted from [Tom Swartz's AdventOfCodeLeaderboard](https://github.com/tomswartz07/AdventOfCodeLeaderboard), this bot will post to Slack when members of a private leaderboard have earned new stars. It will also post the leaderboard if wanted, sorting by score, breaking ties by stars.

Usage
-----

Regardless of how you run you'll need to gather a few items first.

1. __Leaderboard ID:__ This can be found in the url when viewing your leaderboard.

    ```text
    https://adventofcode.com/YYYY/leaderboard/private/view/[LEADERBOARD ID]
    ```

2. __Session Cookie:__ While logged in to [Advent of Code](https://adventofcode.com):

    _In Firefox:_
    - Open the Developer Tools by pressing `F12`
    - Click on the small gear on the top right of the Developer Options pane
    - Scroll down and make sure that "Storage" is checked under the Default Firefox Developer Options section
    - Click on the Storage tab
    - Open the Cookies section and copy the "Value" for "session"

    _In Chrome:_
    - Open the Developer Tools by pressing `CTRL` + `Shift` + `I` or `Cmd` + `Opt` + `I` on Mac
    - Select "Application" from the tool tabs
    - Click the dropdown arrow beside cookies to expand it
    - Select *https://adventofcode.com*
    - Copy the "Value" for "session"

    __These session cookies last for about a month, so grab it close to December 1st.__

3. __Slack Webhook:__ Follow the instructions [HERE](https://slack.com/help/articles/115005265063-Incoming-webhooks-for-Slack) to create a new webhook for a channel of your choice.

Once you have gathered these items update the `env` file accordingly.

### Running Locally

```bash
pip3 install -r requirements.txt
export $(grep -v '^#' env | xargs)
./advent-of-code-bot.py [leaderboard]
```

### Running in Docker

1. Update the crontab to your desired schedule. Defaults to checking for new stars every 30 minutes and posts the leaderboard at 7am.

2. Build the container.

    ```bash
    docker build -t advent-of-code-bot:$(cat VERSION.md) .
    ```

3. Run the container.

    ```bash
    docker run -n advent-of-code-bot --env-file env -d advent-of-code-bot:$(cat VERSION.md)
    ```

4. Stop the contaner.

    ```bash
    docker stop advent-of-code-bot
    ```

### Running in K3s on Raspberry Pi 4 Cluster

Yeah this is a bit specific but it's what I'm doing. Should be very easy to adapt to another setup and I may eventually rework it into a Helm chart along with some other niceties. PRs are welcome.

```bash
# update the crontab as desired
# build for 64bit arm raspberry pi 4's
make rpi4-container
# push the generated image up to one of the cluster nodes (do this for each node...)
scp advent-of-code-bot-1.0.0.tar <k3s-node>:~/
# hop onto the cluster node and import the image (do this for each node...)
ssh <k3s-node> "sudo k3s ctr images import ./advent-of-code-bot-1.0.0.tar"
# stub out a namespace
kubectl create namespace advent-of-code-bot
# generate secrets
kubectl create secret generic advent-of-code-bot-secret \
  --namespace advent-of-code-bot \
  --from-literal='leaderboard_id=<LEADERBOARD_ID>' \
  --from-literal='slack_webhook=<SLACK_WEBHOOK>' \
  --from-literal='session_cookie=<SESSION_COOKIE>'
# deploy the rest
kubectl apply -f advent-of-code-bot.yml
```

Some commands that will come in handy:

```bash
# tear everything down
kubectl delete namespace advent-of-code-bot
# delete the image from k3s
ssh <k3s-node> "sudo k3s ctr images rm docker.io/library/advent-of-code-bot:1.0.0"
# jump onto the pod to poke around
kubectl exec --stdin --tty -n advent-of-code-bot <POD_ID> -- sh
# update secrets (you'll need to base64 encode the new values)
kubectl -n advent-of-code-bot edit secrets advent-of-code-bot-secret
# cycle the pod to get a new image or load in the new secrets
kubectl -n advent-of-code-bot delet pod <POD_ID>
```
