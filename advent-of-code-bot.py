#!/usr/bin/env python3
#
# Advent-of-Code Bot
#
# Pulls down a private leaderboard from adventofcode.com and posts messages to
# Slack when folks earn stars. If `leaderboard` is passed as the first argument
# it will also post the current leaderboard as ordered by points, ties broken
# by stars. Adapted from https://github.com/tomswartz07/AdventOfCodeLeaderboard.
#
# ./advent-of-code-bot.py                   # just grab the data
# ./advent-of-code-bot.py stars             # post any newly earned stars
# ./advent-of-code-bot.py leaderboard       # post the leaderboard
# ./advent-of-code-bot.py leaderboard stars # post new stars and the leaderboard

import os
import sys
import json
import datetime
import requests
import logging as log

from os.path import exists

################################################################################
##                                                                            ##
##  Configuration                                                             ##
##                                                                            ##
################################################################################

slack_bot_icon = ":christmas_tree:"
slack_bot_username = "Advent of Code Bot"

STATE_FILE = os.environ.get('STATE_FILE')
SESSION_ID = os.environ.get('SESSION_ID')
SLACK_WEBHOOK = os.environ.get('SLACK_WEBHOOK')
LEADERBOARD_ID = os.environ.get('LEADERBOARD_ID')

EVENT_YEAR = str(datetime.datetime.today().year)

LEADERBOARD_URL = "https://adventofcode.com/{}/leaderboard/private/view/{}".format(
    EVENT_YEAR,
    LEADERBOARD_ID)

log.basicConfig(
    level=log.INFO,
    format='%(asctime)s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

################################################################################
##                                                                            ##
##  Function                                                                  ##
##                                                                            ##
################################################################################


def parse_members(members_json: dict) -> dict:
    """
    Parse Advent-of-Code members dict into a name indexed dict.
    """
    members = {m['name']: m['stars'] for m in members_json.values()}

    return members


def order_members(members_json: dict) -> list:
    """
    Parse and order members by their score into a list.
    """
    # get member name, score and stars
    members = [(m["name"],
                m["local_score"],
                m["stars"]
                ) for m in members_json.values()]

    # sort members by score, descending
    members.sort(key=lambda s: (-s[1], -s[2]))

    return members


def build_new_star_messages(old_state: dict, new_state: dict) -> list:
    """
    Build a list of messages for folks who have earned at least 1 new star.
    """
    messages = []
    for member, stars in new_state.items():
        old_count = old_state.get(member) if old_state.get(member) else 0
        new_stars = stars - old_count
        if new_stars > 0:
            announcement = f"{member} earned {new_stars} new star{'s'[:new_stars^1]}!"
            messages.append(f":star2: {announcement}")
            log.info(f" - {announcement}")

    return messages


def build_leaderboard_message(members):
    """
    Format the message to conform to Slack's API.
    """
    message = ""

    # add each member to message
    medals = [':third_place_medal:', ':second_place_medal:', ':first_place_medal:']
    for username, score, stars in members:
        if medals:
            medal = medals.pop()
        else:
            medal = ':christmas_tree:'
        message += f"{medal} *{username}*  (points: {score}  stars: {stars})\n"

    message += f"\n<{LEADERBOARD_URL}|View Leaderboard Online>"

    return message


def post_to_slack(message: str, header: str = None):
    """
    Post the message to Slack.
    """
    payload = {
        "icon_emoji": slack_bot_icon,
        "username": slack_bot_username,
    }

    if header:
        payload['blocks'] = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": header,
                    "emoji": True,
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message,
                }
            },
        ]
    else:
        payload['text'] = message

    r = requests.post(
        SLACK_WEBHOOK,
        data=json.dumps(payload),
        timeout=60,
        headers={"Content-Type": "application/json"}
    )
    if r.status_code != requests.codes.ok:
        log.error(f"Error posting to Slack, received {r.status_code}")
        sys.exit(1)


################################################################################
##                                                                            ##
##  Main                                                                      ##
##                                                                            ##
################################################################################


def main():
    log.info("Starting run")

    ##############
    #  validate  #
    ##############

    log.debug("Checking for required environment variables")
    if LEADERBOARD_ID == "" or SESSION_ID == "" or SLACK_WEBHOOK == "" or STATE_FILE == "":
        log.error("Missing required environment variables")
        sys.exit(1)

    ############################
    #  query adventofcode.com  #
    ############################

    log.info(f"Grabbing private leaderboard ID {LEADERBOARD_ID}")
    r = requests.get(
        "{}.json".format(LEADERBOARD_URL),
        timeout=60,
        cookies={"session": SESSION_ID}
    )
    if r.status_code != requests.codes.ok:
        log.error(f"Error retrieving the leaderboard, received {r.status_code}")
        sys.exit(1)

    ###################
    #  read in state  #
    ###################

    state_file = {}
    if exists(STATE_FILE):
        log.info(f"Loading last saved state from {STATE_FILE}")
        with open(STATE_FILE) as m:
            try:
                state_file = json.load(m)
            except json.decoder.JSONDecodeError:
                log.warning("Unable to decode the state file, starting fresh")
    else:
        log.info("State file not found, starting fresh")

    #########################
    #  calculate the bits   #
    #########################

    log.debug("Determining new state from the leaderboard")
    old_state = state_file[EVENT_YEAR] if EVENT_YEAR in state_file else {}
    new_state = parse_members(r.json()['members'])

    log.info("Checking for new stars")
    messages = build_new_star_messages(old_state, new_state)

    log.debug(f"Saving the new state to {STATE_FILE}")
    state_file[EVENT_YEAR] = new_state
    with open(STATE_FILE, 'w') as f:
        json.dump(state_file, f)

    #################
    #  slack posts  #
    #################

    if len(messages) and "stars" in sys.argv:
        log.info("Announcing new stars on Slack")
        post_to_slack('\n'.join(messages))

    if "leaderboard" in sys.argv:
        log.info("Preparing the leaderboard")
        members = order_members(r.json()["members"])
        message = build_leaderboard_message(members)
        log.info("Posting the leaderboard to Slack")
        post_to_slack(message, ":star2: Today's Leaderboard :star2:")

    log.info("Run complete")


if __name__ == "__main__":
    main()
