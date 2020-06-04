# Pocket.RAR - Pocket Random Article Retriever
App for getpocket.com that gets random article in queue, allow skipping specific tags

## Setup

### requirements.txt

### API access
* https://getpocket.com/developer/apps/new
* platform=web
* get *CONSUMER KEY* and update config.yml

### Hosting
* optionally change port in config.yml
* host app with internet routable callback URL set in config.yml (eg. use caddy with some public domain)
