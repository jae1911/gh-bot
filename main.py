import logging

from flask import Flask

# Setup logging
logger = logging.getLogger('main')

# Endpoints
from handlers.gitlab import gitlab_api
from handlers.github import github_api

# Main app
app = Flask(__name__)

# Endpoints
app.register_blueprint(gitlab_api)
app.register_blueprint(github_api)

if __name__ == '__main__':
    app.run()
    app.warn('Starting app')
