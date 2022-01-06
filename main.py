import logging
import json
import hashlib
import hmac
import os

from flask import Flask, request
import requests
import markdown

app = Flask(__name__)

log = logging.getLogger('app')

# Get env variables
SEC_TOKEN = os.environ.get('SEC_TOKEN')
MATRIX_TOKEN = os.environ.get('MATRIX_TOKEN')
MATRIX_HOMESERVER = os.environ.get('MATRIX_HOMESERVER')

@app.post('/gh/webhook')
def gh_webhook():
    # Test if we got environment variables
    if not SEC_TOKEN or not MATRIX_TOKEN or not MATRIX_HOMESERVER:
        return 'err', 510

    # Get request JSON
    json_data = request.json

    # Get headers
    event_type = request.headers.get('X-Github-Event')
    event_sig = request.headers.get('X-Hub-Signature-256')

    if not event_sig:
        return 'wrong auth', 401

    webhook_token = bytes(SEC_TOKEN, 'UTF-8')
    signature = hmac.new(webhook_token, request.data, hashlib.sha256)

    full_sig = f'sha256={signature.hexdigest()}'

    if event_sig != full_sig:
        return 'signature mismatch', 401

    res_string = ''
    send_message = False

    # Get repository data
    repo = json_data.get('repository')

    # Get basic repository infos
    repo_name = repo['name']
    repo_url = repo['html_url']
    repo_visibility = repo['private']
    if repo_visibility:
        repo_visibility = 'private'
    else:
        repo_visibility = 'public'

    res_string += f'Repository [{repo_name}]({repo_url}) ({repo_visibility}) received a {event_type} event.  \n'

    # If event is 'push'
    if event_type == 'push':
        # Get head commit data
        head_commit = json_data.get('head_commit')

        head_id = head_commit['id']
        head_timestamp = head_commit['timestamp']
        head_author = head_commit['author']['name']
        head_url = head_commit['url']
        head_message = head_commit['message']

        res_string += f'Head commit: [{head_id}]({head_url}) at {head_timestamp} by {head_author}: "{head_message}".  \n'

        # Get commits data
        commits_list = json_data.get('commits')

        res_string += f'List of commits included:  \n'

        commit_dict = {}
        # Process all commits included
        for commit in commits_list:
            commit_id = commit['id']
            commit_url = commit['url']
            commit_author = commit['author']['name']
            commit_message = commit['message']

            res_string += f' - [[{commit_id}]({commit_url}) - {commit_author}] "{commit_message}"  \n'

        # No error, no halt, send message
        send_message = True
    elif event_type == 'workflow_run':
        # Workflow
        workflow_run = json_data.get('workflow_run')

        workflow_status = workflow_run['status']
        workflow_name = workflow_run['name']
        workflow_conclusion = workflow_run['conclusion']
        workflow_url = workflow_run['url']
        workflow_attempts = workflow_run['run_attempt']

        if workflow_status == 'completed':
            if workflow_conclusion == 'failure':
                res_string += f'Workflow {workflow_name} has failed!  [See the details to know why.]({workflow_url})  '
            else:
                res_string += f'Workflow {workflow_name} completed successfully with {workflow_attempts} attempts.  '

            send_message = True
        else:
            # We ignore other statuses as the bot is already spammy as it is
            res_string = 'OK'
    elif event_type == 'issues':
        # Issue
        issue_data = json_data.get('issue')

        issue_title = issue_data['title']
        issue_opener = issue_data['user']['login']
        issue_url = issue_data['html_url']
        issue_number = issue_data['number']

        issue_action = json_data.get('action')

        ignore_actions = ['labeled', 'unlabeled', 'unpinned', 'pinned']
        if issue_action in ignore_actions:
            # We ignore that
            res_string = 'ok'
            log.warn(f'Ignoring issue event for {repo_name}#{issue_number} because of {issue_action}')
        else:
            res_string += f'Issue #{issue_number} ("[{issue_title}]({issue_url})") was {issue_action} by {issue_opener}'
            send_message = True
    else:
        # If a certain event isn't implemented, we log it
        log.warn(f'{event_type} is not implemented')
        res_string = 'OK'

    if send_message:
        payload = {
            'msgtype': 'm.notice',
            'body': res_string,
            'format': 'org.matrix.custom.html',
            'formatted_body': markdown.markdown(res_string)
        }

        r = requests.get(f'https://{MATRIX_HOMESERVER}/_matrix/client/v3/joined_rooms?access_token={MATRIX_TOKEN}')

        if r.status_code != 200:
            log.error(f'Something bad happened: {r.text}')
            return "err", 500

        joined_rooms = json.loads(r.text)
        for room in joined_rooms.get('joined_rooms'):
            msg = f'https://{MATRIX_HOMESERVER}/_matrix/client/r0/rooms/{room}/send/m.room.message?access_token={MATRIX_TOKEN}'
            r = requests.post(msg, data=json.dumps(payload))
            if r.status_code != 200:
                log.error(f'Something bad happened: {r.text}')
                return "err", 500

    return res_string, 200
