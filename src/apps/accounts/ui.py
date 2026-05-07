ADMIN_UI_MODE = "admin"
USER_UI_MODE = "user"
UI_MODE_SESSION_KEY = "ui_mode"


def get_user_interface_mode(request):
    if not request.user.is_authenticated:
        return USER_UI_MODE

    if not request.user.is_administrator:
        return USER_UI_MODE

    selected_mode = request.session.get(UI_MODE_SESSION_KEY)
    if selected_mode == ADMIN_UI_MODE:
        return ADMIN_UI_MODE
    return USER_UI_MODE


def set_user_interface_mode(request, mode):
    normalized_mode = ADMIN_UI_MODE if mode == ADMIN_UI_MODE else USER_UI_MODE

    if normalized_mode == ADMIN_UI_MODE and not request.user.is_administrator:
        normalized_mode = USER_UI_MODE

    request.session[UI_MODE_SESSION_KEY] = normalized_mode
    return normalized_mode
