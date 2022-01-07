import logging

from flask_apscheduler import APScheduler
from flask import Flask

# Flask config
class Config:
    SCHEDULER_TIMEZONE = 'Europe/Helsinki'

# Setup logging
logger = logging.getLogger('main')

# Scheduler
from utils.roomutil import check_matrix_rooms_for_joins

# Endpoints
from handlers.gitlab import gitlab_api
from handlers.github import github_api
from handlers.gitea import gitea_api

# Main app
app = Flask(__name__)
app.config.from_object(Config())

# Scheduler
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

# Add scheduler to auto-join Matrix rooms
@scheduler.task('interval', id='join_rooms', seconds=15)
def join_rooms():
    logger.warn('Running the join_rooms task.')
    check_matrix_rooms_for_joins()

# Endpoints
app.register_blueprint(gitlab_api)
app.register_blueprint(github_api)
app.register_blueprint(gitea_api)

if __name__ == '__main__':
    app.run()
    app.warn('Starting app')
