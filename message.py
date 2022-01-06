import os

import requests
import markdown

# ENV variables
MATRIX_TOKEN = os.environ.get('MATRIX_TOKEN')
MATRIX_HOMESERVER = os.environ.get('MATRIX_HOMESERVER')

def send_message(message=None):
    if message == None:
        return False

    payload = {
        'msgtype': 'm.notice',
        'body': message,
        'format': 'org.matrix.custom.html',
        'formatted_body': markdown.markdown(message)
    }

    r = requests.get(f'https://{MATRIX_HOMESERVER}/_matrix/client/v3/joined_rooms?access_token={MATRIX_TOKEN}')

    if r.status_code != 200:
        log.error(f'Something bad happened: {r.text}')
        return False

    joined_rooms = json.loads(r.text)
    for room in joined_rooms.get('joined_rooms'):
        msg = f'https://{MATRIX_HOMESERVER}/_matrix/client/r0/rooms/{room}/send/m.room.message?access_token={MATRIX_TOKEN}'
        r = requests.post(msg, data=json.dumps(payload))
        if r.status_code != 200:
            log.error(f'Something bad happened: {r.text}')
            return False
    return True
