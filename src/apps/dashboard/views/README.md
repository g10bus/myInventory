# `dashboard/views`

Папка хранит вьюхи главной страницы и аналитики.

Содержимое:
- `web.py` — redirect с root, home dashboard и admin analytics.
- `__init__.py` — технический файл пакета.

Как это работает:
- View-слой здесь тонкий: почти вся подготовка данных идёт через `selectors.py`.
- Это хороший пример aggregator-style app, где HTTP-слой минимален, а логика сосредоточена в запросах.
