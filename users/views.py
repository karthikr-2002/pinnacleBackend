from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Value
from django.db.models.functions import Concat
from .forms import UserLoginForm, UserRegisterForm, EmployeeCreateForm, EmployeeEditForm, EmployeeResetPasswordForm, UserProfileForm, UserSelfPasswordChangeForm
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

    search_query = request.GET.get('q', '').strip()
    employees = (
        User.objects.exclude(role='admin')
        .exclude(is_superuser=True)
        .prefetch_related('assigned_units')
        .order_by('first_name', 'last_name', 'username')
    )
    if search_query:
        employees = employees.annotate(
            full_name_search=Concat('first_name', Value(' '), 'last_name')
        ).filter(
            Q(first_name__icontains=search_query)
            | Q(last_name__icontains=search_query)
            | Q(full_name_search__icontains=search_query)
        )
    return render(request, 'users/admin/employee_list.html', {
        'employees': employees,
        'search_query': search_query,
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
        'submit_label': 'Create Employee',
        'is_edit': False,
        'employee': None,
        'active_menu': 'employees',
    })


@login_required(login_url='users:login')
def employee_edit(request, pk):
    if not is_admin(request.user):
        raise PermissionDenied('Only administrators can edit employee accounts.')

    from evaluations.models import Unit
    employee = get_object_or_404(
        User.objects.exclude(role='admin').exclude(is_superuser=True),
        pk=pk,
    )
    units = Unit.objects.all().order_by('name')

    if request.method == 'POST':
        form = EmployeeEditForm(request.POST, request.FILES, instance=employee)
        if form.is_valid():
            employee = form.save()
            messages.success(
                request,
                f"Employee '{employee.display_name}' was updated."
            )
            return redirect('employees:list')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = EmployeeEditForm(instance=employee)

    return render(request, 'users/admin/employee_form.html', {
        'form': form,
        'units': units,
        'title': 'Edit Employee',
        'submit_label': 'Save Changes',
        'is_edit': True,
        'employee': employee,
        'active_menu': 'employees',
    })


@login_required(login_url='users:login')
def employee_reset_password(request, pk):
    if not is_admin(request.user):
        raise PermissionDenied('Only administrators can reset employee passwords.')

    employee = get_object_or_404(
        User.objects.exclude(role='admin').exclude(is_superuser=True),
        pk=pk,
    )

    if request.method == 'POST':
        form = EmployeeResetPasswordForm(employee, request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f"Password for employee '{employee.display_name}' (@{employee.username}) was successfully reset."
            )
            return redirect('employees:list')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = EmployeeResetPasswordForm(employee)

    return render(request, 'users/admin/employee_reset_password.html', {
        'form': form,
        'employee': employee,
        'title': 'Reset Employee Password',
        'active_menu': 'employees',
    })


@login_required(login_url='users:login')
def profile_view(request):
    """View and update current user's profile details and password."""
    user = request.user
    user_units = user.assigned_units.all()
    show_edit_modal = 'edit' in request.GET
    show_password_modal = 'password' in request.GET

    profile_form = UserProfileForm(instance=user)
    password_form = UserSelfPasswordChangeForm(user)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'edit_profile':
            profile_form = UserProfileForm(request.POST, request.FILES, instance=user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Your profile details have been updated successfully.")
                return redirect('users:profile')
            messages.error(request, "Please correct the errors in the profile form.")
            show_edit_modal = True
        elif action == 'change_password':
            password_form = UserSelfPasswordChangeForm(user, request.POST)
            if password_form.is_valid():
                password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Your password has been changed successfully.")
                return redirect('users:profile')
            messages.error(request, "Please correct the errors in the password form.")
            show_password_modal = True

    return render(request, 'users/profile.html', {
        'profile_form': profile_form,
        'password_form': password_form,
        'user_obj': user,
        'user_units': user_units,
        'show_edit_modal': show_edit_modal,
        'show_password_modal': show_password_modal,
        'active_menu': 'profile',
    })
