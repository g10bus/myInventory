# `workflows`

В этой папке лежат pipeline-файлы GitHub Actions.

Содержимое:
- `ci.yml` — основной CI для Django-проекта.

Как это работает:
- Workflow поднимает Python `3.12`.
- Зависимости ставятся из `requirements/prod.txt`.
- Далее выполняются `manage.py check`, миграции, `bootstrap_roles`, `collectstatic` и проверка, что нет неприменённых изменений моделей.
- Среда для CI использует `config.settings.test` и SQLite, поэтому pipeline не зависит от production PostgreSQL.
