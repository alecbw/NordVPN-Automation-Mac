
# import subprocess, re, random, datetime
from subprocess import Popen, PIPE

import logging
import argparse
import random
from datetime import datetime, timedelta
from time import sleep
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def execute_applescript(scpt, args=[]):
    p = Popen(['osascript', '-'] + args, stdin=PIPE, stdout=PIPE, stderr=PIPE, universal_newlines=True) # universal_newlines avoids the need to use bytes
    stdout, stderr = p.communicate(scpt)
    if stderr:
        logging.error(stderr)

    return stdout


# Note: connecting can take 2-10 seconds
def connect_to_configuration_by_name(configuration_name):
    result = execute_applescript('tell application "/Applications/Tunnelblick.app" to connect "' + configuration_name + '"')
    logging.info(f"Status of connecting was {result}")


def list_configurations():
    return execute_applescript('tell application "/Applications/Tunnelblick.app" to get configurations')


# Note: disconnecting can take 2-3 seconds
def disconnect_configurations():
    result = execute_applescript('tell application "/Applications/Tunnelblick.app" to disconnect all')
    logging.info(f"Status of disconnecting was {result}")


def set_configuration_auth(configuration_name, username, password):
    execute_applescript('tell application "/Applications/Tunnelblick.app" to save username "' + username + '" for "' + configuration_name + '"')
    execute_applescript('tell application "/Applications/Tunnelblick.app" to save password "' + password + '" for "' + configuration_name + '"')


def rotate_configuration(connection_list):
    disconnect_configurations()
    next_configuration_idx = random.randrange(0, len(connection_list)-1)
    next_configuration = connection_list[next_configuration_idx]
    set_configuration_auth(next_configuration, os.environ['NORD_USER'], os.environ['NORD_PASS'])
    connect_to_configuration_by_name(next_configuration)


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-refresh_rate', required=True, help="In minutes")
    args = argparser.parse_args()

    raw_configurations = list_configurations()
    connection_list = [x.replace("configuration ", "").strip() for x in raw_configurations.split(",")]

    logging.info(f"{len(connection_list)} connections found")

    rotate_configuration(connection_list)

    randomized_time = datetime.now() + timedelta(minutes=random.randrange(1,int(args.refresh_rate)))
    logging.info(f"Will roll the proxy config at {randomized_time}")

    while True:
        try:
            if datetime.now() >= randomized_time:
                rotate_configuration(connection_list)
                randomized_time = datetime.now() + timedelta(minutes=random.randrange(1,int(args.refresh_rate)))
                logging.info(f"Will roll the proxy config at {randomized_time}")
            sleep(1)

        except KeyboardInterrupt:
            disconnect_configurations()
            break
