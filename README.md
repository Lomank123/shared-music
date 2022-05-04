# shared-music
Shared Music service provides you comfortable rooms where you can listen to music with friends or anyone else who wants to come in. All you have to do is click create room button and share the link. It's that simple! See all the features below.

The main goal was to use WebSocket protocol with Django web framework and channels lib.

## Badges

Here should be some badges... (WIP)


## Table of contents

- [shared-music](#shared-music)
  - [Badges](#badges)
  - [Table of contents](#table-of-contents)
  - [Requirements (Prerequisites)](#requirements-prerequisites)
  - [Installation](#installation)
    - [Docker setup](#docker-setup)
    - [Local setup (without Docker containers)](#local-setup-without-docker-containers)
  - [Screenshots](#screenshots)
  - [Features](#features)
    - [Main features](#main-features)
    - [Tech features](#tech-features)
    - [Room owner features:](#room-owner-features)
  - [Usage](#usage)
    - [Run project](#run-project)
    - [Linters](#linters)
    - [Fixtures](#fixtures)
  - [Tests](#tests)
    - [Tests description](#tests-description)
  - [Deployment](#deployment)
  - [Tech stack](#tech-stack)
  - [Authors](#authors)


## Requirements (Prerequisites)

- Python v3.9 [Install](https://www.python.org/downloads/release/python-390/)
- Docker [Install](https://www.docker.com/products/docker-desktop)
- Git [Install](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)


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

### Docker setup

- Build everything:
```
docker-compose build
``` 

For the first time it may take 5-20 minutes to build everything (depends on your internet connection and PC hardware)


### Local setup (without Docker containers)

- venv setup:
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

Insert some screenshots


## Features

### Main features
- Create room in one click
- Invite anyone by sharing the link
- Load tracks from YouTube (other services WIP)
- User's playlist (WIP)
- Save/Load room playlist (WIP)
- Download urls from room's or user's playlist (WIP)
- Communicate by sending messages to in-room chat (WIP)
    - Private messages included

### Tech features
- WebSocket protocol to keep changes in rooms

### Room owner features:
- Set permissions to limit some actions (WIP)
    - Who can change track
    - Who can vote for change
    - Enable/Disable vote for change
- Ban, kick or mute listeners if it is needed (WIP)
- Transfer ownership to any listener (WIP)


## Usage

### Run project

- Locally:
```
cd sharedmusic
py manage.py runserver
```

- Using Docker:
```
docker-compose up
```

### Linters
- To run linters:

### Fixtures
- To fill the database:

- Superuser:
    - email: `admin@gmail.com`
    - password: `12345`
- User 1:
    - email: `test1@gmail.com`
    - password: `123123123Aa`
- User 2:
    - email: `test2@gmail.com`
    - password: `123123123Qq`


## Tests

- To run tests:


### Tests description


## Deployment

Assuming remote host OS is Linux, and Docker, docker-compose and Git have been installed recently:

- Enter remote host's console via ssh:
```
ssh -l username ip-address 
```
Fill in password after this command.

- Follow [installation](#installation) guide

- To run production version you should use:
```
docker-compose -f docker-compose-deploy.yml up
```


## Tech stack

- **Backend**:
    - Django
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

- [Lomank123](https://github.com/Lomank123)
- [erikgab01](https://github.com/erikgab01)