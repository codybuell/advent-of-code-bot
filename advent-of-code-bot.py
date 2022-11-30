#!/usr/bin/env python3
#
# Advent-of-Code Bot
#
# Pulls down a private leaderboard from adventofcode.com and posts messages to
# Slack when folks earn stars. If `leaderboard` is passed as the first argument
# it will also post the current leaderboard as ordered by points, ties broken
# by stars. Adapted from https://github.com/tomswartz07/AdventOfCodeLeaderboard.
#
# ./advent-of-code-bot.py [leaderboard]

import os
import sys
import json
import datetime
import requests

from os.path import exists

################################################################################
##                                                                            ##
##  Configuration                                                             ##
##                                                                            ##
################################################################################

STATE_FILE = os.environ.get('STATE_FILE')
SESSION_ID = os.environ.get('SESSION_ID')
SLACK_WEBHOOK = os.environ.get('SLACK_WEBHOOK')
LEADERBOARD_ID = os.environ.get('LEADERBOARD_ID')

LEADERBOARD_URL = "https://adventofcode.com/{}/leaderboard/private/view/{}".format(
    datetime.datetime.today().year,
    LEADERBOARD_ID)

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
            messages.append(f":star2: {member} earned {new_stars} new star{'s'[:new_stars^1]}!")

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
        "icon_emoji": ":christmas_tree:",
        "username": "Advent of Code Bot",
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

    requests.post(
        SLACK_WEBHOOK,
        data=json.dumps(payload),
        timeout=60,
        headers={"Content-Type": "application/json"}
    )


################################################################################
##                                                                            ##
##  Main                                                                      ##
##                                                                            ##
################################################################################


def main():
    # check for required variables
    if LEADERBOARD_ID == "" or SESSION_ID == "" or SLACK_WEBHOOK == "" or STATE_FILE == "":
        print("Please update script variables before running script.\n\
                See README for details on how to do this.")
        sys.exit(1)

    # grab current leaderboard
    r = requests.get(
        "{}.json".format(LEADERBOARD_URL),
        timeout=60,
        cookies={"session": SESSION_ID}
    )
    if r.status_code != requests.codes.ok:  # pylint: disable=no-member
        print("Error retrieving leaderboard")
        sys.exit(1)

    # grab old state
    if exists(STATE_FILE):
        with open(STATE_FILE) as m:
            old_state = json.load(m)
    else:
        old_state = {}

    # grab new state
    new_state = parse_members(r.json()['members'])

    # build new stars list
    messages = build_new_star_messages(old_state, new_state)

    # save the new state
    with open(STATE_FILE, 'w') as f:
        json.dump(new_state, f)

    # if we have any new stars, announce
    if len(messages):
        post_to_slack('\n'.join(messages))

    # if leaderboard specified build and post
    if len(sys.argv) > 1 and sys.argv[1] == 'leaderboard':
        # build ordered list of members
        members = order_members(r.json()["members"])
        message = build_leaderboard_message(members)
        post_to_slack(message, ":star2: Today's Leaderboard :star2:")


if __name__ == "__main__":
    main()
