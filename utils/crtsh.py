import os

import redis
import feedparser

# Get Domains
DOMAINS_CRT = os.environ.get('CRT_DOMAINS')

def get_feeds():
    if not DOMAINS_CRT:
        return None

    # Create list from domains
    domain_list = DOMAINS_CRT.split(',')

    for domain in domain_list:
        feed = feedparser.parse(f'https://crt.sh/atom?q={domain}')
