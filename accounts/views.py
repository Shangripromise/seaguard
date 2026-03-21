from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required

from .forms import RegisterForm, LoginForm
from vessels.models import Vessel
from emergencies.models import EmergencyRequest
from providers.models import RecoveryProvider, ProviderRating


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
    vessels = Vessel.objects.filter(owner=request.user)
    emergencies = EmergencyRequest.objects.filter(
        submitted_by=request.user
    ).select_related('vessel', 'assigned_provider').order_by('-created_at')
    active_emergencies = emergencies.filter(status='active')
    context = {
        'vessels':            vessels,
        'emergencies':        emergencies,
        'active_emergencies': active_emergencies,
    }
    return render(request, 'accounts/dashboard.html', context)


@staff_member_required
def admin_dashboard(request):
    total_users        = User.objects.count()
    total_vessels      = Vessel.objects.count()
    total_emergencies  = EmergencyRequest.objects.count()
    active_emergencies = EmergencyRequest.objects.filter(
        status='active'
    ).select_related('vessel', 'assigned_provider')
    reported_emergencies = EmergencyRequest.objects.filter(
        status='reported'
    ).select_related('vessel')
    pending_ratings = ProviderRating.objects.filter(
        moderation_status='pending'
    ).count()
    pending_providers = RecoveryProvider.objects.filter(
        verification_status='pending'
    ).count()
    context = {
        'total_users':           total_users,
        'total_vessels':         total_vessels,
        'total_emergencies':     total_emergencies,
        'active_emergencies':    active_emergencies,
        'reported_emergencies':  reported_emergencies,
        'pending_ratings':       pending_ratings,
        'pending_providers':     pending_providers,
    }
    return render(request, 'accounts/admin_dashboard.html', context)


@login_required
def member_discounts(request):
    """
    CR3 — Member Discounts page.
    FR-VO-DISC-001: accessible to authenticated vessel operators.
    FR-VO-DISC-002: blocked during any active emergency request.
    """
    # Check for active emergency — redirect away if one exists
    active_emergency = EmergencyRequest.objects.filter(
        submitted_by=request.user,
        status='active'
    ).first()

    if active_emergency:
        messages.warning(
            request,
            'Member discounts are not available during an active emergency. '
            'Please wait until your emergency is resolved.'
        )
        return redirect('emergencies:emergency_detail', pk=active_emergency.pk)

    # Static discount offers — in production these would come from a database
    # model. For MVP they are hardcoded per SRS scope constraint C-12.
    discounts = [
        {
            'partner':      'Berthon Boat Co.',
            'category':     'Marine Services',
            'offer':        '10% off annual vessel servicing',
            'code':         'SEAGUARD10',
            'valid_until':  'Dec 2026',
        },
        {
            'partner':      'Pantaenius UK',
            'category':     'Marine Insurance',
            'offer':        '15% discount on new yacht insurance policies',
            'code':         'SG-PANT15',
            'valid_until':  'Jun 2026',
        },
        {
            'partner':      'Force 4 Chandlery',
            'category':     'Marine Equipment',
            'offer':        '12% off safety equipment orders over £100',
            'code':         'SGFORCE12',
            'valid_until':  'Dec 2026',
        },
        {
            'partner':      'RYA Training',
            'category':     'Training & Certification',
            'offer':        '£50 off any RYA practical course',
            'code':         'SGRYATRN',
            'valid_until':  'Sep 2026',
        },
        {
            'partner':      'Fuel Marine',
            'category':     'Fuel & Lubricants',
            'offer':        '8p per litre discount on marina fuel',
            'code':         'SGFUEL8',
            'valid_until':  'Dec 2026',
        },
    ]

    return render(request, 'accounts/member_discounts.html', {
        'discounts': discounts,
    })