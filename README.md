# shared-music

![Alt text](./sharedmusic/main/static/images/sharedmusic_black.svg)

**Shared Music** service provides you rooms where you can listen to music with friends or anyone else who wants to come in. All you have to do is click create room button and share the link. It's that simple! See all the features [here](#features).

**Main goals:**
- Provide useful service which will let anyone create music rooms for shared listening and communicating
- Construct WebSocket-based application
- Gain team work experience

Live version can be visited at: [sharedmusic.live](https://sharedmusic.live/)


[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![codecov](https://codecov.io/gh/Lomank123/shared-music/branch/main/graph/badge.svg?token=371L2PBI81)](https://codecov.io/gh/Lomank123/shared-music)


## Table of contents

- [shared-music](#shared-music)
  - [Table of contents](#table-of-contents)
  - [Requirements (Prerequisites)](#requirements-prerequisites)
  - [Installation](#installation)
    - [Docker setup](#docker-setup)
    - [Local setup (without Docker containers)](#local-setup-without-docker-containers)
  - [Screenshots](#screenshots)
  - [Features](#features)
    - [Main features](#main-features)
    - [Tech features](#tech-features)
    - [Room host features](#room-host-features)
  - [Usage](#usage)
    - [Run project](#run-project)
      - [Locally](#locally)
      - [Using Docker](#using-docker)
    - [Fixtures](#fixtures)
      - [`dev.json` fixtures contain](#devjson-fixtures-contain)
      - [Users credentials](#users-credentials)
    - [Backup](#backup)
    - [Restore](#restore)
  - [Tests](#tests)
    - [Tests description](#tests-description)
  - [Deployment](#deployment)
  - [Tech stack](#tech-stack)
  - [Authors](#authors)


## Requirements (Prerequisites)

- Python v3.9 [Install](https://www.python.org/downloads/release/python-390/)
- Docker [Install](https://www.docker.com/products/docker-desktop)
- Git [Install](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- Redis [Install](https://redis.io/docs/getting-started/)


## Installation

- Clone repository:
```
git clone https://github.com/Lomank123/shared-music.git
```

- Go to project root folder, create `.env` file and copy the contents of `.env.sample` to it.

For Linux:
```
cd path/to/project/shared-music
cp .env.sample .env
```

Create `/backups` folder (if you want to use backups):
```
mkdir backups
```

### Docker setup

- Open `/sharedmusic/sharedmusic/settings/settings.py` and find `CHANNEL_LAYERS` variable. Replace
```
"hosts": [(REDIS_HOST, 6379)],
```
with
```
"hosts": [('redis', 6379)],
```

- Build everything:
```
docker-compose build
``` 

For the first time it may take 5-20 minutes to build everything (depends on your internet connection and PC hardware)


### Local setup (without Docker containers)

- First, set appropriate channel layer. In `/sharedmusic/sharedmusic/settings/settings.py` you can find `CHANNEL_LAYERS`:
```
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'main.channel_layers.CustomChannelLayer',
        'CONFIG': {
            "hosts": [(REDIS_HOST, 6379)],
        },
    },
}
```

- There are 2 supported ones:
  - `channels.layers.InMemoryChannelLayer`
  - `main.channel_layers.CustomChannelLayer` - custom implementation of `channels_redis.pubsub.RedisPubSubChannelLayer`

- Next is `venv` setup:
```
mkdir venv
cd venv
py -m venv ./venv
```

- Install requirements:
```
pip install -r requirements.txt
```

- Create Postgres db and user (credentials should be the same as in `.env` file)

- Also change `DB_HOST` env var in `.env` file from `'db'` to `'localhost'`:
```
DB_HOST=localhost
```

- Go to `/sharedmusic` dir:
```
cd sharedmusic
```

-  Migrations:
```
py manage.py makemigrations
py manage.py migrate
```

- Create superuser:
```
py manage.py createsuperuser
```


## Screenshots

- Home page:

![Home page](./sharedmusic/main/static/images/readme/home_page.png)

- Navbar:

![Navbar](./sharedmusic/main/static/images/readme/navbar.png)

- Authorization:

![Authorization](./sharedmusic/main/static/images/readme/auth.png)

- Room page:

![Room page](./sharedmusic/main/static/images/readme/room_page.png)

- Mobile version

![Mobile version](./sharedmusic/main/static/images/readme/mobile.png)


## Features

### Main features
- Create room in one click
- Invite anyone by sharing the link
- Communicate by sending messages to room chat
- *Load tracks from YouTube (other services WIP)*
- *User playlist (WIP)*
- *Save/Load room playlist (WIP)*
- *Download urls from room or user playlist (WIP)*

### Tech features
- CI/CD
- Both asgi and wsgi apps (daphne and gunicorn) to serve `http` and `WebSocket` connections.
- WebSocket protocol to keep changes in rooms
- Nginx reverse proxy to serve static files and WebSockets
- Celery tasks
  -  To remove abandoned rooms (periodically)

### Room host features
- Change permissions
  - change/add/delete track
  - pause/play track
  - change time of current track
- Transfer ownership to any listener
- Ban/unban any listener
- Mute/unmute any listener


## Usage

### Run project

#### Locally

- Run `Redis` if you use `CustomChannelLayer`

- Run these commands:
```
cd sharedmusic
py manage.py runserver
```

#### Using Docker

- Run:
```
docker-compose up
```

### Fixtures
- To fill the database:
```
docker-compose up filldb
```

#### `dev.json` fixtures contain
  - Superuser
  - Regular user
  - Room
  - Room playlist
  - Soundtrack
  - Room playlist track
  - Chat messages

#### Users credentials
  - Superuser:
    - username: `admin`
    - password: `12345`
  - User:
    - username: `test1`
    - password: `123123123Aa`

### Backup
- Assuming you have created `/backups` dir you can just run `pgbackups` container
```
docker-compose up pgbackups
```

If you want to configure it follow [here](https://github.com/prodrigestivill/docker-postgres-backup-local#environment-variables)

### Restore
- Run db container
```
docker-compose up db
```

- Enter there via docker exec sh:
```
docker exec -t -i shared-music_db_1 sh
```

- In db container create backups folder:
```
mkdir backups
```

- Copy backup file to db container (here I used path from my pc):
```
docker cp D:\path\to\folder\backups\last\backupfile.sql.gz shared-music_db_1:/backups
```

Replace `backupfile.sql.gz` with your actual backup file name (located at `backups\last` for example)

- Run restoration command (replace `$USERNAME` and `$DBNAME` with `.env` variables (`DB_USER` and `DB_NAME`), and also `$BACKUPFILE` with previously copied file name)
```
docker exec --tty --interactive shared-music_db_1 /bin/sh -c "zcat backups/$BACKUPFILE | psql --username=$USERNAME --dbname=$DBNAME -W"
```

- Enter password (`DB_PASS` variable in `.env`)

- Check restored db


## Tests

- To run tests:
```
docker-compose up test
```

### Tests description

These tests cover:
- channels Consumers
- Services
- Celery tasks
- Views

Services and consumers tests run using `InMemoryChannelLayer`.

## Deployment

Assuming remote host OS is Linux, and Docker, docker-compose and Git have been installed recently:

- Enter remote host's console via ssh (where `IP` is your host ip address):
```
ssh -l username IP
```
Fill in password after this command.

- Follow [installation](#installation) guide

- To run production version you should use:
```
docker-compose -f docker-compose-deploy.yml up
```


## Tech stack

- **Backend**:
  - Django 3
  - channels
  - Redis
  - Gunicorn
  - Daphne
  - PostgreSQL
  - Coverage
  - Celery
  - Nginx
- **Frontend**:
  - YouTube API
  - jQuery
- **Other**:
  - GitHub
  - Codecov
  - Docker
  - docker-compose


## Authors

- [Lomank123](https://github.com/Lomank123) - Backend
- [erikgab01](https://github.com/erikgab01) - Frontend
