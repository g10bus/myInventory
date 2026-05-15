# `src`

Это корневая папка Django-приложения и связанных с ним runtime-ресурсов.

Содержимое:
- `apps/` — доменные приложения modular monolith.
- `config/` — конфигурация Django, settings и маршрутизация верхнего уровня.
- `static/` — CSS, JS и изображения.
- `templates/` — HTML-шаблоны интерфейса.

Как это работает:
- `manage.py` и Django settings добавляют `src` в рабочий импортный контекст.
- Python-код из `apps/` и `config/` формирует бизнес-логику и web-слой.
- `templates/` и `static/` подключаются через Django templates и staticfiles.
