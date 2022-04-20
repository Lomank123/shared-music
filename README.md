# shared-music
Shared listening to music with others

**(WIP)**


## Badges

Here should be some badges...


## Table of contents

Place table of contents here


## Requirements (Prerequisites)

- Python v3.9 [Install](https://www.python.org/downloads/release/python-390/)
- Docker [Install](https://www.docker.com/products/docker-desktop)


## Installation

- Clone repository:
```
git clone https://github.com/Lomank123/shared-music.git
```

- Go to project root folder, create `.env` file and copy the contents of `.env.sample` to it. Replace some variables if needed.

- Create `venv` directory, go to it and run
```
py -m venv ./venv
```

- Install requirements:
```
pip install -r requirements.txt
```

- Create Postgres db and user or change default db engine in `settings/settings.py` (credentials should be the same as in .env file)

- Migrations:
```
py manage.py makemigrations
py manage.py migrate
```

- Go to `/sharedmusic` dir and run:
```
py manage.py runserver
```


## Screenshots

Insert some screenshots


## Features

Describe features


## Usage

### Run project
- To run project:
```
cd sharedmusic
py manage.py runserver
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


## Tech stack

- **Backend**:
    - Django
    - channels
    - Redis
    - Gunicorn
    - PostgreSQL
    - Coverage
- **Frontend**:
    -
- **Other**:
    - GitHub
    - Codecov


## Author

See my GitHub profile for further information: [profile link](https://github.com/Lomank123)