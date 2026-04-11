# My Inventory

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.2-092E20?logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![Status](https://img.shields.io/badge/status-production--only-2ea44f)

Внутренняя Django-система для учета материальных ценностей предприятия, закрепленных за сотрудниками.

## Production Запуск

### 1. Подготовить окружение

```bash
cp .env.example .env
```

### 2. Поднять сервисы

```bash
docker compose -f compose.prod.yaml up --build -d
```

### 3. Применить миграции и подготовить роли

```bash
docker compose -f compose.prod.yaml exec web python manage.py migrate
docker compose -f compose.prod.yaml exec web python manage.py bootstrap_roles
```

### 4. Создать суперпользователя

```bash
docker compose -f compose.prod.yaml exec web python manage.py createsuperuser
```

## Архитектура

Проект организован как `modular monolith` с доменными apps:

- `apps.accounts` — пользователи и аутентификация.
- `apps.org` — оргструктура и отделы.
- `apps.inventory` — карточки ТМЦ.
- `apps.custody` — выдача, возврат, передача.
- `apps.audit` — журнал событий.
- `apps.dashboard` — агрегаты главной панели.
- `apps.core` — инфраструктура и health endpoints.

## Основные Команды

```bash
make migrate
make makemigrations
make collectstatic
make createsuperuser
make bootstrap-roles
make check
make shell
make backup
make restore FILE=./var/backups/backup.sql
```
