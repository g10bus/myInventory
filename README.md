# My Inventory

[![CI](https://github.com/g10bus/myInventory/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/g10bus/myInventory/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.2-092E20?logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![Architecture](https://img.shields.io/badge/architecture-modular%20monolith-1f6feb)
![Status](https://img.shields.io/badge/status-internal%20system-2ea44f)

Внутренняя Django-система для учета материальных ценностей предприятия: карточек ТМЦ, закрепления за сотрудниками, передачи, возврата, инвентаризаций и интеграций с внешними системами.

## Что умеет система

- вести каталог ТМЦ с инвентарными и серийными номерами;
- закреплять оборудование за сотрудниками и возвращать его в резерв;
- оформлять передачу ТМЦ между сотрудниками;
- назначать периоды инвентаризации и сохранять фотофиксации сверки;
- хранить аудит ключевых действий;
- импортировать отделы, сотрудников и ТМЦ из 1С;
- поддерживать локальный вход и доменную аутентификацию через Active Directory.

## Технологический стек

- `Python 3.12`
- `Django 5.2`
- `PostgreSQL 16`
- `Docker Compose`
- `WhiteNoise` для раздачи статических файлов
- `django-environ` для конфигурации через переменные окружения

## Архитектура

Проект организован как `modular monolith` с доменными Django apps:

- `apps.accounts` — пользователи, профиль, аутентификация, режим администратора.
- `apps.org` — отделы и оргсправочники.
- `apps.inventory` — карточки ТМЦ, сверки и назначения инвентаризации.
- `apps.custody` — выдача, возврат и передача ТМЦ.
- `apps.audit` — единый журнал событий.
- `apps.integrations` — 1С, Active Directory и технические журналы синхронизации.
- `apps.dashboard` — главная панель и агрегированная аналитика.
- `apps.core` — инфраструктурные модели, access guards, PDF и management-команды.

Внутри приложений проект в основном разделён на:

- `models.py` — структура данных;
- `selectors.py` — чтение и агрегация данных для UI;
- `services.py` — изменения состояния и бизнес-операции;
- `views/web.py` — HTTP-слой;
- `forms.py` — формы и валидация пользовательского ввода.

## Структура репозитория

```text
.
├── .github/              # CI workflow
├── docker/               # entrypoint и gunicorn config
├── docs/                 # проектная документация
├── requirements/         # зависимости Python
├── scripts/              # backup/restore базы
├── src/
│   ├── apps/             # доменные Django apps
│   ├── config/           # settings, urls, asgi/wsgi
│   ├── static/           # CSS, JS, изображения
│   └── templates/        # HTML шаблоны
├── compose.prod.yaml
├── Dockerfile
├── Makefile
└── manage.py
```

Во все основные каталоги проекта добавлены локальные `README.md` с описанием содержимого и механики работы.

## Быстрый запуск в Docker

### 1. Подготовить окружение

```bash
cp .env.example .env
```

Минимально важные переменные:

- `DJANGO_SETTINGS_MODULE=config.settings.prod`
- `DJANGO_SECRET_KEY=...`
- `DATABASE_URL=postgres://inventory:inventory@db:5432/inventory`
- `DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1`

### 2. Поднять сервисы

```bash
docker compose -f compose.prod.yaml up --build -d
```

Что произойдет:

- поднимется `db` на `PostgreSQL 16`;
- поднимется `web` на Django + Gunicorn;
- контейнер дождётся готовности базы;
- при старте автоматически выполнятся `migrate` и `collectstatic`.

### 3. Подготовить роли доступа

```bash
docker compose -f compose.prod.yaml exec web python manage.py bootstrap_roles
```

### 4. Создать суперпользователя

```bash
docker compose -f compose.prod.yaml exec web python manage.py createsuperuser
```

### 5. Открыть приложение

```text
http://localhost:8000
```

## Локальная разработка

Базовые команды через `Makefile`:

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

Примечания:

- `Makefile` использует `python3`.
- Для локального запуска вне Docker нужны установленные зависимости из `requirements/`.
- По умолчанию базовые settings читают `.env` через `django-environ`.

## Тесты и CI

CI описан в `.github/workflows/ci.yml` и выполняет:

- установку зависимостей;
- `python manage.py check`;
- `python manage.py migrate --noinput`;
- `python manage.py bootstrap_roles`;
- `python manage.py collectstatic --noinput`;
- `python manage.py makemigrations --check --dry-run`.

Для CI используется:

- `DJANGO_SETTINGS_MODULE=config.settings.test`
- `SQLite` как тестовая база

## Интеграции

### 1С

- экран настройки: `integrations/manage/`
- ручной запуск синхронизации:

```bash
python manage.py sync_one_c_data
```

Синхронизируются:

- отделы;
- сотрудники;
- карточки ТМЦ.

### Active Directory

- экран настройки: `integrations/manage/`
- проверка подключения:

```bash
python manage.py test_active_directory_connection
```

Поддерживается:

- вход по локальному email/password;
- вход по доменному логину Active Directory;
- синхронизация профиля пользователя при логине, если это включено в настройках.

## Данные и эксплуатация

Резервное копирование:

```bash
make backup
```

Восстановление:

```bash
make restore FILE=./var/backups/backup.sql
```

Скрипты используют `pg_dump` и `psql`, поэтому должны выполняться в окружении, где доступны PostgreSQL client tools и корректный `DATABASE_URL`.

## Документация

Дополнительные материалы лежат в `docs/`:

- `database_architecture.md`

## Замечания по проекту

- Это server-rendered Django-приложение, а не SPA.
- Статические файлы обслуживаются через `WhiteNoise`.
- Media-файлы пользователей и фотофиксаций сохраняются в `var/media`.
- Бизнес-история действий опирается на `apps.audit`.
