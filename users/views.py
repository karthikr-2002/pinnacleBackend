from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from .forms import UserLoginForm, UserRegisterForm, EmployeeCreateForm
from .models import User


def is_admin(user):
    return user.is_authenticated and (user.is_superuser or getattr(user, 'role', '') == 'admin')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            remember_me = form.cleaned_data.get('remember_me')
            login(request, user)

            if remember_me:
                request.session.set_expiry(1209600)  # 2 weeks
            else:
                request.session.set_expiry(0)  # On browser close

            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('dashboard:index')
        else:
            messages.error(request, "Invalid username or password. Please check your credentials.")
    else:
        form = UserLoginForm()

    return render(request, 'users/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been successfully logged out.")
    return redirect('users:login')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Account created successfully! Welcome, {user.first_name}!")
            return redirect('dashboard:index')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserRegisterForm()

    return render(request, 'users/register.html', {'form': form})


@login_required(login_url='users:login')
def employee_list(request):
    if not is_admin(request.user):
        raise PermissionDenied('Only administrators can manage employees.')

    employees = (
        User.objects.exclude(role='admin')
        .exclude(is_superuser=True)
        .prefetch_related('assigned_units')
        .order_by('first_name', 'last_name', 'username')
    )
    return render(request, 'users/admin/employee_list.html', {
        'employees': employees,
        'active_menu': 'employees',
    })


@login_required(login_url='users:login')
def employee_create(request):
    if not is_admin(request.user):
        raise PermissionDenied('Only administrators can create employee accounts.')

    from evaluations.models import Unit
    units = Unit.objects.all().order_by('name')

    if request.method == 'POST':
        form = EmployeeCreateForm(request.POST, request.FILES)
        if form.is_valid():
            employee = form.save()
            unit = form.cleaned_data['unit']
            messages.success(
                request,
                f"Employee '{employee.display_name}' ({employee.employee_id}) created and assigned to {unit.name}."
            )
            return redirect('employees:list')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = EmployeeCreateForm()

    return render(request, 'users/admin/employee_form.html', {
        'form': form,
        'units': units,
        'title': 'Create Employee',
        'active_menu': 'employees',
    })
