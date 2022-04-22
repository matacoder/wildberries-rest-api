# WB Rest Client
<img src=https://raw.githubusercontent.com/matacoder/matacoder/main/wb_rest.png>

Get access to all endpoints of wildberries marketplace.

Live version is here: [wb.matakov.com](https://wb.matakov.com)

## What is included

- Live stock quantity
- Today's orders
- Today's sales
- 14 days' sales
- Cart
- What to buy next analysis

## How to test:

1) Register
2) Set up your API KEY
3) All done. Know what to buy to keep stock and top sellers

# How to run locally?

1) Install Docker for your OS
2) Run `cmd` or `Windows Powershell`
3) Navigate to folder with cloned repository
4) Create `.env`, as template you may use [this example](https://github.com/matacoder/django-docker/blob/master/.env)
5) Run `docker compose up`
6) Site will run at `127.0.0.1:1112`


# Как запустить на моем компьютере?

1) Установите Docker для вашей операционной системы
2) Запустите `cmd` или `Windows Powershell`
3) Склонируйте репозиторий и перейдите в его папку
4) Создайте файл `.env`, за основу можно взять [образец отсюда](https://github.com/matacoder/django-docker/blob/master/.env)
5) Запустите `docker compose up`
6) Сайт будет доступен по адресу: `127.0.0.1:1112`

# Environment variables (переменные окружения)

Save them to `.env` file (сохраните их в файл)

* DB_ENGINE=django.db.backends.postgresql
* DB_NAME=postgres
* POSTGRES_USER=postgres
* POSTGRES_PASSWORD=please_use_secure_password
* DB_HOST=db
* DB_PORT=5432
* SECRET_KEY=please_use_secure_password
* DJANGO_SUPERUSER_PASSWORD=please_use_secure_password
* DJANGO_SUPERUSER_EMAIL=example@example.com
* DJANGO_SUPERUSER_USERNAME=admin
* DOCKER_USERNAME=matakov
* DOCKER_IMAGE=wb
* DEBUG=1
* REDIS_PASSWORD=please_use_secure_password