# Fishing store

## Description
Will be shown soon...


## How to run localy
1. Prerequisties (Linux)
    - Python 3.14+ (pip, virtualenv)
    - Docker 29.4+
    - Git

2. Clone the repository
``` bash
git clone git@github.com:Solidarov/fishing-store.git
```

3. Create docker volume for Postgres container database
```bash
docker volume create db_data
```

4. Rewrite environment varibles in `.env` or use the mocking one that already provided

5. Run container
```bash
docker compose up --build
```

6. The app will be available in the browser under the `http:/localhost:8000/` address