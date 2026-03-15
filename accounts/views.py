from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from .forms import RegisterForm, LoginForm
from vessels.models import Vessel
from emergencies.models import EmergencyRequest


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('dashboard')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name}!')
            return redirect('dashboard')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')


@login_required
def dashboard_view(request):
    return render(request, 'accounts/dashboard.html')


@staff_member_required
def admin_dashboard(request):
    total_users = User.objects.count()
    total_vessels = Vessel.objects.count()
    total_emergencies = EmergencyRequest.objects.count()
    active_emergencies = EmergencyRequest.objects.filter(status='active')

    context = {
        'total_users': total_users,
        'total_vessels': total_vessels,
        'total_emergencies': total_emergencies,
        'active_emergencies': active_emergencies,
    }
    return render(request, 'accounts/admin_dashboard.html', context)
