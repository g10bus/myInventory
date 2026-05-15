# `templates`

Здесь лежат HTML-шаблоны всех web-страниц проекта.

Содержимое:
- Базовый шаблон: `base.html`.
- Аутентификация и профиль: `login.html`, `register.html`, `profile.html`, `confirm_admin_mode.html`.
- Dashboard и аналитика: `main.html`, `analytics.html`.
- Инвентарь: `tmc.html`, `tmc_detail.html`, `inventory_admin.html`, `inventory_create.html`, `inventory_edit.html`, `inventory_assignment_admin.html`.
- Закрепление и передача: `history.html`, `exchange.html`, `custody_admin.html`.
- Администрирование: `user_admin.html`, `user_edit.html`, `org_admin.html`, `integrations_admin.html`.
- Общие include: `include/`.

Как это работает:
- Django view возвращает context, после чего шаблон рендерит итоговую HTML-страницу.
- Основная композиция строится через `base.html`, а частные страницы переопределяют блоки.
- Шаблоны тесно связаны с именами context-переменных из `views/web.py`.
