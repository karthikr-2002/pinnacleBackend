from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from .forms import UserLoginForm, UserRegisterForm


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
