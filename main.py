import logging
import json
import hashlib
import hmac
import os

from flask import Flask, request

from message import send_to_matrix

app = Flask(__name__)

# Setup logging
github_log = logging.getLogger('github')
gitlab_log = logging.getLogger('gitlab')

# Get env variables
SEC_TOKEN = os.environ.get('SEC_TOKEN')

# Github
@app.post('/gh/webhook')
def gh_webhook():
    # Test if we got environment variables
    if not SEC_TOKEN:
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

    # If event is 'push'
    if event_type == 'push':
        # Get commits data
        commits_list = json_data.get('commits')

        res_string += f'Repo [{repo_name}]({repo_url}) received a push containing {len(commits_list)} commits:  \n'

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
        res_string += f'[{repo_name}] '

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
            github_log.warn(f'Ignoring issue event for {repo_name}#{issue_number} because of {issue_action}')
        else:
            res_string += f'[{repo_name}] Issue #{issue_number} ("[{issue_title}]({issue_url})") was {issue_action} by {issue_opener}'
            send_message = True
    elif event_type == 'pull_requests':
        # Pull Request
        pr_data = json_data.get('pull_request')

        pr_url = pr_data['html_url']
        pr_title = pr_data['title']
        pr_opener = pr_data['user']['login']
        pr_number = pr_data['number']

        pr_action = json_data.get('action')
        ignore_actions = ['auto_merge_disabled', 'auto_merge_enabled', 'synchronize', 'unlabeled', 'labeled']

        if pr_action in ignore_actions:
            res_string = 'ok'
        else:
            res_string += f'{pr_opener} {pr_action} PR [{pr_number} "{pr_title}"]({pr_url})'
            send_message = True
    elif event_type == 'star':
        # Star
        star_action = json_data.get('action')
        if star_action == 'deleted':
            res_string = 'ok'
        else:
            star_sender = json_data.get('sender')
            star_timestamp = json_data.get('starred_at')
            star_giver = star_sender['login']
            res_string += f'{star_giver} starred {repo_name} on {star_timestamp}.'
            send_message = True
    elif event_type == 'release':
        res_string += f'[{repo_name}] '

        # Release
        rel_data = json_data.get('release')

        rel_url = rel_data['html_url']
        rel_name = rel_data['tag_name']
        rel_maker = rel_data['author']['login']

        rel_action = json_data.get('action')

        if rel_action == 'published':
            res_string += f'{rel_maker} created the [{rel_name}]({rel_url}) release.'
            send_message = True
        else:
            res_string = 'ok'
    elif event_type == 'issue_comment':
        # Issue comment
        ic_data = json_data.get('comment')

        ic_url = ic_data['html_url']
        ic_commenter = ic_data['user']['login']
        ic_text = ic_data['body']

        ic_issue_title = json_data.get('issue')['title']
        ic_issue_number = json_data.get('issue')['number']

        ic_action = json_data.get('action')

        if ic_action == 'created':
            res_string += f'{ic_commenter} commented on issue [{repo_name}#{ic_issue_number}]({ic_url}) "{ic_issue_title}":  \n> {ic_text}'
            send_message = True
        else:
            res_string = 'ok'
    elif event_type == 'discussion':
        # Discussion
        ds_data = json_data.get('discussion')

        ds_url = ds_data['html_url']
        ds_number = ds_data['number']
        ds_title = ds_data['title']
        ds_opener = ds_data['user']['login']

        ds_action = json_data.get('action')
        if ds_action == 'created':
            res_string += f'{ds_opener} opened a new discussion {repo_name}#{ds_number}: ["{ds_title}"]({ds_url})'
            send_message = True
        else:
            res_string = 'ok'
    elif event_type == 'sponsorship':
        # Sponsorship
        sp_data = json_data.get('sponsorship')

        sp_created = sp_data['created_at']

        sp_sa_name = sp_data['sponsorable']['login']
        sp_sp_name = sp_data['sponsored']['login']
        sp_tier_name = sp_data['tier']['name']
        sp_tier_price = sp_data['tier']['monthly_price_in_dollars']

        sp_action = json_data.get('action')
        if sp_action == 'created':
            res_string += f'{sp_sa_name} has sponsored {sp_sp_name} with a {sp_tier_name} tier ({sp_tier_price})!'
            send_message = True
        else:
            res_string = 'ok'
    elif event_type == 'package':
        # Package
        pkg_data = json_data.get('package')

        pkg_name = pkg_data['namespace']
        pkg_url = pkg_data['html_url']
        pkg_eco = pkg_data['ecosystem']
        pkg_tag = pkg_data['package_version']['target_commitish']

        pkg_action = json_data.get('action')

        res_string += f'[{pkg_name}:{pkg_tag}]({pkg_url}) ({pkg_eco}) got {pkg_action}'
        send_message = True
    else:
        # If a certain event isn't implemented, we log it
        github_log.warn(f'{event_type} is not implemented')
        res_string = 'OK'

    if send_message:
        send_to_matrix(res_string)

    return res_string, 200

# Gitlab
@app.post('/gl/webhook')
def gl_webhook():
    # Test env variable
    if not SEC_TOKEN:
        return 'err', 510

    # Get data
    json_data = request.json

    # Get headers
    event_sig = request.headers.get('X-Gitlab-Token')

    if not json_data or not event_sig:
        return 'err', 510

    # Check token
    if event_sig != SEC_TOKEN:
        return 'err', 510

    # Get event type
    event_type = json_data.get('event_name')

    # Default strings
    send_message = False
    res_string = ''

    # Handle events
    if event_type == 'push':
        # Push
        user_trigger = json_data.get('user_name')

        # Project
        project_data = json_data.get('project')
        project_url = project_data['web_url']
        project_name = project_data['name']

        # Commits
        included_commits = json_data.get('commits')

        # Build string
        res_string += f'Repository [{project_name}]({project_url}) got {len(included_commits)} new commits pushed by {user_trigger}:  \n'
        for commit in included_commits:
            commit_id = commit['id']
            commit_author = commit['author']['name']
            commit_message = commit['message']

            res_string += f' - [{commit_id} - {commit_author}] "{commit_message}"  '

        send_message = True
    else:
        gitlab_log.warn(f'{event_type} is not implemented')

    if send_message:
        send_to_matrix(res_string)

    return 'ok', 200
