from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Value
from django.db.models.functions import Concat
from django.core.paginator import Paginator
from .forms import (
    UserLoginForm, UserRegisterForm, EmployeeCreateForm, EmployeeEditForm,
    EmployeeResetPasswordForm, UserProfileForm, UserSelfPasswordChangeForm,
    AdminProfileEditForm
)
from .models import User, AuditLog
from .security import (
    get_client_ip, check_login_lockout, record_login_failure, record_login_success,
    admin_required, is_admin_user
)
from .audit import log_audit_event


def is_admin(user):
    return is_admin_user(user)


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    ip_address = get_client_ip(request)
    context = {}

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()

        # 1. Check if user or IP is currently locked out
        is_locked, remaining_mins, remaining_secs, reason = check_login_lockout(username, ip_address)
        if is_locked:
            log_audit_event(
                'LOGIN_LOCKED',
                request=request,
                target_repr=username,
                details={'locked_minutes': remaining_mins, 'reason': reason}
            )
            messages.error(
                request,
                f"Too many failed login attempts ({reason}). "
                f"Access has been temporarily locked for security. "
                f"Please try again in {remaining_mins} minute(s)."
            )
            context.update({
                'form': UserLoginForm(request),
                'is_locked': True,
                'remaining_minutes': remaining_mins,
            })
            return render(request, 'users/login.html', context)

        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            # Clear any failed attempt counter on success
            record_login_success(username, ip_address)

            remember_me = form.cleaned_data.get('remember_me')
            login(request, user)

            log_audit_event(
                'LOGIN_SUCCESS',
                request=request,
                actor=user,
                target=user,
                details={'remember_me': bool(remember_me)}
            )

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
            # Login failed - record attempt and evaluate lockout threshold
            is_locked, remaining_attempts, remaining_mins = record_login_failure(username, ip_address)
            if is_locked:
                log_audit_event(
                    'LOGIN_LOCKED',
                    request=request,
                    target_repr=username,
                    details={'locked_minutes': remaining_mins, 'reason': 'Failed attempts threshold reached'}
                )
                messages.error(
                    request,
                    f"Too many failed login attempts. "
                    f"This account has been temporarily locked for {remaining_mins} minutes for security."
                )
                context.update({
                    'is_locked': True,
                    'remaining_minutes': remaining_mins,
                })
            else:
                log_audit_event(
                    'LOGIN_FAILED',
                    request=request,
                    target_repr=username,
                    details={'remaining_attempts': remaining_attempts, 'reason': 'Invalid credentials'}
                )
                messages.error(
                    request,
                    f"Invalid username or password. "
                    f"{remaining_attempts} attempt(s) remaining before temporary account lockout."
                )
                context.update({
                    'remaining_attempts': remaining_attempts,
                })
            context['form'] = form
    else:
        # GET request - check if IP is locked
        is_locked, remaining_mins, remaining_secs, reason = check_login_lockout('', ip_address)
        if is_locked:
            context.update({
                'is_locked': True,
                'remaining_minutes': remaining_mins,
            })
        context['form'] = UserLoginForm()

    return render(request, 'users/login.html', context)


def logout_view(request):
    if request.user.is_authenticated:
        log_audit_event(
            'LOGOUT',
            request=request,
            actor=request.user,
            target=request.user,
            details={'username': request.user.username}
        )
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


@admin_required
def employee_list(request):
    search_query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip().lower()

    base_qs = (
        User.objects.exclude(role='admin')
        .exclude(is_superuser=True)
        .prefetch_related('assigned_units')
    )

    total_count = base_qs.count()
    active_count = base_qs.filter(is_active=True).count()
    inactive_count = base_qs.filter(is_active=False).count()

    employees = base_qs.order_by('first_name', 'last_name', 'username')

    if search_query:
        employees = employees.annotate(
            full_name_search=Concat('first_name', Value(' '), 'last_name')
        ).filter(
            Q(first_name__icontains=search_query)
            | Q(last_name__icontains=search_query)
            | Q(full_name_search__icontains=search_query)
            | Q(employee_id__icontains=search_query)
        )

    if status_filter == 'active':
        employees = employees.filter(is_active=True)
    elif status_filter == 'inactive':
        employees = employees.filter(is_active=False)

    return render(request, 'users/admin/employee_list.html', {
        'employees': employees,
        'search_query': search_query,
        'status_filter': status_filter,
        'total_count': total_count,
        'active_count': active_count,
        'inactive_count': inactive_count,
        'active_menu': 'employees',
    })


@admin_required
def employee_create(request):
    from evaluations.models import Unit
    units = Unit.objects.all().order_by('name')

    if request.method == 'POST':
        form = EmployeeCreateForm(request.POST, request.FILES)
        if form.is_valid():
            employee = form.save()
            unit = form.cleaned_data['unit']
            log_audit_event(
                'USER_CREATED',
                request=request,
                target=employee,
                details={
                    'employee_id': employee.employee_id,
                    'username': employee.username,
                    'unit': unit.name,
                    'is_active': employee.is_active,
                }
            )
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


@admin_required
def employee_edit(request, pk):
    from evaluations.models import Unit
    employee = get_object_or_404(
        User.objects.exclude(role='admin').exclude(is_superuser=True),
        pk=pk,
    )
    units = Unit.objects.all().order_by('name')

    if request.method == 'POST':
        old_is_active = employee.is_active
        form = EmployeeEditForm(request.POST, request.FILES, instance=employee)
        if form.is_valid():
            employee = form.save()
            if old_is_active != employee.is_active:
                log_audit_event(
                    'USER_STATUS_CHANGED',
                    request=request,
                    target=employee,
                    details={
                        'old_active': old_is_active,
                        'new_active': employee.is_active,
                        'status': employee.status_label
                    }
                )
            log_audit_event(
                'USER_UPDATED',
                request=request,
                target=employee,
                details={'updated_by': request.user.username}
            )
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


@admin_required
def employee_reset_password(request, pk):
    employee = get_object_or_404(
        User.objects.exclude(role='admin').exclude(is_superuser=True),
        pk=pk,
    )

    if request.method == 'POST':
        form = EmployeeResetPasswordForm(employee, request.POST)
        if form.is_valid():
            form.save()
            log_audit_event(
                'PASSWORD_RESET',
                request=request,
                target=employee,
                details={'reset_by_admin': request.user.username}
            )
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
    user_is_admin = is_admin(user)

    if user_is_admin:
        profile_form = AdminProfileEditForm(instance=user)
    else:
        profile_form = UserProfileForm(instance=user)

    password_form = UserSelfPasswordChangeForm(user)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'edit_profile':
            if user_is_admin:
                profile_form = AdminProfileEditForm(request.POST, request.FILES, instance=user)
            else:
                profile_form = UserProfileForm(request.POST, request.FILES, instance=user)

            if profile_form.is_valid():
                profile_form.save()
                log_audit_event(
                    'USER_UPDATED',
                    request=request,
                    target=user,
                    details={'self_service': True, 'is_admin': user_is_admin}
                )
                messages.success(request, "Your profile details have been updated successfully.")
                return redirect('users:profile')
            messages.error(request, "Please correct the errors in the profile form.")
            show_edit_modal = True
        elif action == 'change_password':
            password_form = UserSelfPasswordChangeForm(user, request.POST)
            if password_form.is_valid():
                password_form.save()
                update_session_auth_hash(request, user)
                log_audit_event(
                    'PASSWORD_CHANGED',
                    request=request,
                    target=user,
                    details={'self_service': True}
                )
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
        'is_admin_user': user_is_admin,
        'active_menu': 'profile',
    })


@admin_required
def audit_log_view(request):
    """
    Admin view: Immutable compliance and security audit trail.
    Supports real-time search, category filtering, and pagination.
    """
    search_query = request.GET.get('q', '').strip()
    action_filter = request.GET.get('action', '').strip()

    audit_qs = AuditLog.objects.all().order_by('-timestamp')

    if action_filter:
        audit_qs = audit_qs.filter(action=action_filter)

    if search_query:
        audit_qs = audit_qs.filter(
            Q(actor_username__icontains=search_query) |
            Q(target_repr__icontains=search_query) |
            Q(target_type__icontains=search_query) |
            Q(ip_address__icontains=search_query) |
            Q(action__icontains=search_query)
        )

    paginator = Paginator(audit_qs, 30)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'users/admin/audit_log.html', {
        'page_obj': page_obj,
        'search_query': search_query,
        'action_filter': action_filter,
        'action_choices': AuditLog.ACTION_CHOICES,
        'total_logs': audit_qs.count(),
        'active_menu': 'audit_log',
    })
