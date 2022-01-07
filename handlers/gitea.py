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

    # Get basic repo data
    repo_data = json_data.get('repository')

    repo_name = repo_data['name']
    repo_full_name = repo_data['full_name']
    repo_url = repo_data['html_url']

    # Get basic pusher data
    pusher_data = json_data.get('pusher')

    pusher_name = pusher_data['full_name']

    # Events handling
    if event_type == 'push':
        # Get commits
        commits_list = json_data.get('commits')

        res_string += f'Repo [{repo_full_name}]({repo_url}) received a push of {len(commits_list)} by {pusher_name}:  \n'

        for commit in commits_list:
            commit_id = commit['id']
            commit_message = commit['message']
            commit_url = commit['url']
            commit_author = commit['author']['name']

            res_string += f'[[{commit_id}]({commit_url}) - {commit_author}] "{commit_message}"  \n'

        send_message = True
    else:
        gitea_log.warn(f'Event {event_type} not implemented')

    if send_message:
        send_to_matrix(res_string)

    return 'ok', 200
