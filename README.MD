# Django + Docker Template
<img src=https://raw.githubusercontent.com/matacoder/matacoder/main/django-docker-sea.png>

This is a magic repository for everyone who wants to start developing and do not want to worry about initial django and docker setup.

## What is included

- Django
- Nginx
- PostgreSQL
- Docker Compose for development
- Docker Compose for production
- Caddy config for fast SSL + domain deploy
- Poetry dependency manager
- Initial entrypoint to take care of django and postgres setup
- Black code formatter

## Why _settings?

Do you know that frustration when you are looking for your setting file directory?

I know! So underscored `_settings` folder is always close to top and easy to find.

## What next step?

Create your app using `python manage.py startapp my_new_app`.

## What You Develop is What You Get

Just `docker compose up` and you will see your development version at `127.0.0.1:1111`

Restart your django container (using Docker GUI) everytime you make a change in app logic.

Django's templates engine is reloading without container needed to restart

## Fast Deploy Using Docker Context

Docker context is a bridge to your remote server to run docker commands on your local pc or mac.

#### STEP 0: Create new context to remote control your server docker (once)
`docker context create new_ip --docker "host=ssh://username@ip"`

#### STEP 1: Build and push your docker image on local PC (use variables in .env)
`docker build -t username/project:latest .` (don't forget dot at the end)

`docker push username/project:latest`

#### STEP 2: Switch to remote server docker
`docker context use new_ip`

#### STEP 3: Down your compose, pull new image, up your compose
`docker compose -f docker-compose-prod.yaml down`

Here consider deleting static volume if you have static files modified

`docker pull username/project:latest`

`docker compose -f docker-compose-prod.yaml up -d --force-recreate`

#### STEP 4: Don't forget to switch back to your local docker
`docker context use default`

# Run your site with Caddy Server

Install [Caddy Server](https://caddyserver.com), replace `example.com` with your domain in `Caddyfile` and run command:

```bash
sudo caddy stop
sudo caddy run
```

Consider adding `caddy` to [linux start up sequence](https://caddy.community/t/want-caddy-to-run-automatically-on-boot/5240).
