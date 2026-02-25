#!/usr/bin/env python3
"""
Railway entrypoint: generates config.yaml from environment variables
and starts imap2imap.
"""
import os
import yaml
from imap2imap import Imap2Imap
from time import sleep
from sys import exit as sys_exit
import signal
import logging

# Logging
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    fmt="[railway] %(asctime)s:%(levelname)s:%(message)s",
    datefmt='%Y-%m-%d %H:%M:%S'
))
log.addHandler(handler)


def generate_config():
    """Generate config dict from environment variables."""
    required = [
        'SRC_HOST', 'SRC_USER', 'SRC_PASSWORD',
        'DEST_HOST', 'DEST_USER', 'DEST_PASSWORD'
    ]
    for var in required:
        if not os.environ.get(var):
            raise ValueError(f"Missing required env var: {var}")

    config = {
        'common': {
            'debug': os.environ.get('DEBUG', 'false').lower() == 'true',
            'sleep': int(os.environ.get('SLEEP_SECONDS', '300')),
            'sleep_var_pct': int(os.environ.get('SLEEP_VAR_PCT', '50'))
        },
        'src_imap': {
            'host': os.environ['SRC_HOST'],
            'ssl': os.environ.get('SRC_SSL', 'true').lower() == 'true',
            'user': os.environ['SRC_USER'],
            'password': os.environ['SRC_PASSWORD'],
            'mailbox': os.environ.get('SRC_MAILBOX', 'INBOX'),
            'on_success': {
                'delete_msg': os.environ.get('ON_SUCCESS_DELETE', 'false').lower() == 'true',
                'move_to_mailbox': os.environ.get('ON_SUCCESS_MOVE_TO') or None,
                'mark_as_seen': os.environ.get('ON_SUCCESS_MARK_SEEN', 'true').lower() == 'true'
            }
        },
        'dest_imap': {
            'host': os.environ['DEST_HOST'],
            'ssl': os.environ.get('DEST_SSL', 'true').lower() == 'true',
            'user': os.environ['DEST_USER'],
            'password': os.environ['DEST_PASSWORD'],
            'mailbox': os.environ.get('DEST_MAILBOX', 'INBOX')
        }
    }
    return config


def main():
    log.info("Starting imap2imap Railway service...")

    # Generate config
    config = generate_config()
    config_path = '/tmp/config.yaml'
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    log.info("Config generated from environment variables")
    log.info("Source: %s -> Destination: %s",
             config['src_imap']['host'],
             config['dest_imap']['host'])

    # Start imap2imap thread
    imap2imap = Imap2Imap(config_path=config_path)
    imap2imap.daemon = True

    def exit_gracefully(sigcode, _frame):
        log.info("Signal %d received, exiting...", sigcode)
        imap2imap.exit_event.set()
        sys_exit(0)

    signal.signal(signal.SIGINT, exit_gracefully)
    signal.signal(signal.SIGTERM, exit_gracefully)

    imap2imap.start()
    log.info("imap2imap thread started")

    # Health check loop
    while True:
        if not imap2imap.healthy():
            log.error("Thread is not healthy, exiting...")
            sys_exit(1)
        sleep(60)


if __name__ == '__main__':
    main()
