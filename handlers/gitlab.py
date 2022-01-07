import logging
import os

from flask import Flask, request, Blueprint

from message import send_to_matrix

# Setup logging
gitlab_log = logging.getLogger('gitlab')

# Get env variables
SEC_TOKEN = os.environ.get('SEC_TOKEN')

gitlab_api = Blueprint('gitlab_api', __name__)

# Gitlab
@gitlab_api.post('/gh/gitlab')
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
    event_type = json_data.get('object_kind')

    # Default strings
    send_message = False
    res_string = ''

    # Project
    project_data = json_data.get('project')
    project_url = project_data['web_url']
    project_name = project_data['name']

    # Handle events
    if event_type == 'push':
        # Push
        user_trigger = json_data.get('user_name')

        # Commits
        included_commits = json_data.get('commits')

        # Build string
        res_string += f'Repository [{project_name}]({project_url}) got {len(included_commits)} new commits pushed by {user_trigger}:  \n'
        for commit in included_commits:
            commit_id = commit['id']
            commit_author = commit['author']['name']
            commit_message = commit['message']
            commit_url = commit['url']

            res_string += f' - [[{commit_id}]({commit_url}) - {commit_author}] "{commit_message}"  \n'

        send_message = True
    elif event_type == 'issue':
        # Issue

        # User data
        user_name = json_data.get('user')['name']

        # Issue data
        is_data = json_data.get('object_attributes')

        is_title = is_data['title']
        is_description = is_data['description']
        is_url = is_data['url']
        is_action = is_data['action']
        is_number = is_data['id']

        if is_action == 'open':
            res_string += f'{user_name} opened the issue [{project_name}#{is_number}]({is_url}): "{is_title}":  \n> {is_description}'
            send_message = True
        elif is_action == 'close':
            res_string += f'{user_name} closed the issue [{project_name}#{is_number}]({is_url})'
            send_message = True
    elif event_type == 'note':
        # Comment

        # User data
        user_name = json_data.get('user')['name']

        # Get comment data
        cm_data = json_data.get('object_attributes')

        cm_content = cm_data['note']
        cm_type = cm_data['noteable_type']
        cm_url = cm_data['url']

        res_string += f'[{user_name} commented on {cm_type}]({cm_url}) - {project_name}  \n> {cm_content}'
    elif event_type == 'merge_request':
        # Merge request

        # User data
        user_name = json_data.get('user')['name']

        # MR data
        mr_data = json_data.get('object_attributes')

        mr_action = mr_data['action']
        mr_id = mr_data['id']
        mr_url = mr_data['url']
        mr_source = mr_data['source_branch']
        mr_target = mr_data['target_branch']

        act = ''
        if mr_action == 'open':
            act = 'opened'
        elif mr_action == 'close':
            act = 'closed'
        elif mr_action == 'reopen':
            act = 'reopened'
        elif mr_action == 'update':
            act = 'updated'
        elif mr_action == 'approved' or mr_action == 'unapproved':
            act = mr_action
        elif mr_action == 'merge':
            act = merged

        res_string += f'{user_name} {act} MR [{mr_id}!{project_name}]({mr_url}) {mr_source}->{mr_target}'
        send_message = True
    elif event_type == 'pipeline':
        # Pipeline status

        # User data
        pip_trigger = json_data.get('user')['name']

        # Pipeline data
        pi_data = json_data.get('object_attributes')

        pi_status = pi_data['status']
        pi_ref = pi_data['ref']
        pi_duration = pi_data['duration']
        pi_id = pi_data['id']

        res_string += f'Pipeline [#{pi_id}]({project_url}/-/pipelines/{pi_id}) finished with code {pi_status} after a {pi_duration}s run on [{repo_name}/{pi_ref}]({repo_url})'
        send_message = True
    else:
        gitlab_log.warn(f'{event_type} is not implemented')

    if send_message:
        send_to_matrix(res_string)

    return 'ok', 200
