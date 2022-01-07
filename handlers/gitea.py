import logging
import os
import hmac
import hashlib

from flask import Flask, request, Blueprint

from message import send_to_matrix

# Setup logging
gitea_log = logging.getLogger('gitea')

# Get env variables
SEC_TOKEN = os.environ.get('SEC_TOKEN')

# Blueprint
gitea_api = Blueprint('gitea_api', __name__)

# Gitea
@gitea_api.post('/gh/gitea')
def gt_webhook():
    # Test if env variables are defined
    if not SEC_TOKEN:
        return 'err', 510

    # Get data
    json_data = request.json

    # Get event type & sig
    event_type = request.headers.get('X-Gitea-Event')
    event_sig = request.headers.get('X-Gitea-Signature')

    # Check for data
    if not json_data or not event_type or not event_sig:
        return 'err', 510

    # Signature check
    webhook_token = bytes(SEC_TOKEN, 'UTF-8')
    signature = hmac.new(webhook_token, request.data, hashlib.sha256)
    full_sig = signature.hexdigest()

    if event_sig != full_sig:
        return 'signature mismatch', 401

    res_string = ''
    send_message = False

    # Events handling
    gitea_log.warn(f'Event {event_type} not implemented')

    if send_message:
        send_to_matrix(res_string)

    return 'ok', 200
