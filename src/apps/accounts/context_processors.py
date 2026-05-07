from .ui import get_user_interface_mode


def interface_mode(request):
    return {
        "ui_mode": get_user_interface_mode(request),
    }
