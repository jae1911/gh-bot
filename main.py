import logging

from flask import Flask

# Setup logging
logger = logging.getLogger('main')

# Endpoints
from handlers.gitlab import gitlab_api
from handlers.github import github_api
from handlers.gitea import gitea_api

# Main app
app = Flask(__name__)

# Endpoints
app.register_blueprint(gitlab_api)
app.register_blueprint(github_api)
app.register_blueprint(gitea_api)

if __name__ == '__main__':
    app.run()
    app.warn('Starting app')
