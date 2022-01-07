import os
import logging
import json

import requests

# Setup logging
room_log = logging.getLogger('roomutil')

# Env variables
MATRIX_TOKEN = os.environ.get('MATRIX_TOKEN')
MATRIX_HOMESERVER = os.environ.get('MATRIX_HOMESERVER')

# Check rooms for joins
def check_matrix_rooms_for_joins():
    # Check for env variables
    if not MATRIX_HOMESERVER or not MATRIX_TOKEN:
        room_log.fatal('NO HOMESERVER ADDRESS NOR TOKEN, CANNOT PROCEED')
        return

    r = requests.get(f'https://{MATRIX_HOMESERVER}/_matrix/client/v3/sync?access_token={MATRIX_TOKEN}')
    if r.status_code == 200:
        json_data = json.loads(r.text)
        rooms = json_data.get('rooms')

        if not 'invite' in rooms:
            room_log.info('No rooms were found in this batch.')
        else:
            for room in rooms['invite']:
                room_log.info(f'Joining room {room}')
                r = requests.post(f'https://{MATRIX_HOMESERVER}/_matrix/client/v3/join/{room}?access_token={MATRIX_TOKEN}')
