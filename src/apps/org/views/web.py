from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from apps.core.access import admin_required
from apps.org.forms import DepartmentCreateForm, LocationCreateForm
from apps.org.models import Department, Location


@login_required
@admin_required
def org_admin_view(request):
    location_form = LocationCreateForm(prefix="location")
    department_form = DepartmentCreateForm(prefix="department")

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "create_location":
            location_form = LocationCreateForm(request.POST, prefix="location")
            if location_form.is_valid():
                location = location_form.save()
                messages.success(request, f"Локация '{location.name}' создана.")
                return redirect("org-admin")
            messages.error(request, "Не удалось создать локацию. Проверьте форму.")

        elif action == "create_department":
            department_form = DepartmentCreateForm(request.POST, prefix="department")
            if department_form.is_valid():
                department = department_form.save()
                messages.success(request, f"Отдел '{department.name}' создан.")
                return redirect("org-admin")
            messages.error(request, "Не удалось создать отдел. Проверьте форму.")

    return render(
        request,
        "org_admin.html",
        {
            "user_data": request.user,
            "location_form": location_form,
            "department_form": department_form,
            "locations": Location.objects.order_by("name"),
            "departments": Department.objects.order_by("name"),
        },
    )
