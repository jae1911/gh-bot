import os
import json

import requests
import markdown

# Get ENV variables
MATRIX_TOKEN = os.environ.get('MATRIX_TOKEN')
MATRIX_HOMESERVER = os.environ.get('MATRIX_HOMESERVER')
LOG_ALL_EVENTS = os.environ.get('LOG_ALL_EVENTS')

# Method to log events to rooms
def log_event_to_rooms(event=None, webhooktype='generic'):
    if not MATRIX_HOMESERVER or not MATRIX_TOKEN or not event:
        return

    payload = {
        'msgtype': f'fi.jae.webhook.{webhooktype}',
        'body': event,
    }

    r = requests.get(f'https://{MATRIX_HOMESERVER}/_matrix/client/v3/joined_rooms?access_token={MATRIX_TOKEN}')

    if r.status_code != 200:
        log.error(f'Something bad happened: {r.text}')
        return

    if not LOG_ALL_EVENTS:
        return

    joined_rooms = json.loads(r.text)
    for room in joined_rooms.get('joined_rooms'):
        msg = f'https://{MATRIX_HOMESERVER}/_matrix/client/r0/rooms/{room}/send/fi.jae.webhooklog?access_token={MATRIX_TOKEN}'
        r = requests.post(msg, data=json.dumps(payload))
        if r.status_code != 200:
            log.error(f'Something bad happened: {r.text}')

# Function to send a message
def send_to_matrix(message=None):
    if not MATRIX_HOMESERVER or not MATRIX_TOKEN or not message:
        return

    payload = {
        'msgtype': 'm.notice',
        'body': message,
        'format': 'org.matrix.custom.html',
        'formatted_body': markdown.markdown(message)
    }

    r = requests.get(f'https://{MATRIX_HOMESERVER}/_matrix/client/v3/joined_rooms?access_token={MATRIX_TOKEN}')

    if r.status_code != 200:
        log.error(f'Something bad happened: {r.text}')
        return

    joined_rooms = json.loads(r.text)
    for room in joined_rooms.get('joined_rooms'):
        msg = f'https://{MATRIX_HOMESERVER}/_matrix/client/r0/rooms/{room}/send/m.room.message?access_token={MATRIX_TOKEN}'
        r = requests.post(msg, data=json.dumps(payload))
        if r.status_code != 200:
            log.error(f'Something bad happened: {r.text}')
