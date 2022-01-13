import os
import logging

import redis
import feedparser

# Setup logging
crtsh_log = logging.getLogger('crtsh')

# Get Domains
DOMAINS_CRT = os.environ.get('CRT_DOMAINS')

def check_new_certificates():
    if not DOMAINS_CRT:
        return None

    # Create list from domains
    domain_list = DOMAINS_CRT.split(',')

    for domain in domain_list:
        feed = feedparser.parse(f'https://crt.sh/atom?q={domain}')
        crtsh_log.warn(feed)
