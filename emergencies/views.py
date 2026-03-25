from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import Http404
from django.utils import timezone

from .models import EmergencyRequest, StatusUpdate
from .forms import EmergencyRequestForm, StatusUpdateForm
from providers.models import RecoveryProvider


def dispatch_best_provider(emergency):
    candidates = RecoveryProvider.objects.filter(
        verification_status='approved',
        is_available=True,
    )
    if not candidates.exists():
        return None
    best_provider = None
    best_score = -1
    for provider in candidates:
        score = provider.ranking_score(
            incident_lat=emergency.latitude,
            incident_lon=emergency.longitude,
            incident_type=emergency.emergency_type,
        )
        if score > best_score:
            best_score = score
            best_provider = provider
    if best_provider:
        emergency.assigned_provider = best_provider
        emergency.status = 'active'
        emergency.last_status_change = timezone.now()
        emergency.save()
        StatusUpdate.objects.create(
            emergency=emergency,
            changed_by=emergency.submitted_by,
            from_status='reported',
            to_status='active',
            notes=f'Auto-dispatched to {best_provider.company_name} (ranking score: {best_score}).',
        )
    return best_provider


@login_required
def emergency_list(request):
    emergencies = EmergencyRequest.objects.filter(
        submitted_by=request.user
    ).select_related('vessel', 'assigned_provider').order_by('-created_at')
    return render(request, 'emergencies/emergency_list.html',
                  {'emergencies': emergencies})


@login_required
def emergency_submit(request):
    if request.method == 'POST':
        form = EmergencyRequestForm(request.user, request.POST)
        if form.is_valid():
            emergency = form.save(commit=False)
            emergency.submitted_by = request.user
            emergency.status = 'reported'
            emergency.last_status_change = timezone.now()
            emergency.save()
            assigned = dispatch_best_provider(emergency)
            if assigned:
                messages.success(
                    request,
                    f'Emergency reported! Auto-dispatched to {assigned.company_name}.'
                )
            else:
                messages.warning(
                    request,
                    'Emergency reported! No providers currently available - '
                    'an administrator has been notified to assign manually.'
                )
            return redirect('emergencies:emergency_list')
    else:
        form = EmergencyRequestForm(request.user)
    return render(request, 'emergencies/emergency_submit.html', {'form': form})


@login_required
def emergency_detail(request, pk):
    emergency = get_object_or_404(EmergencyRequest, pk=pk)
    # Ownership check — staff can see all, users can only see their own
    if not request.user.is_staff and emergency.submitted_by != request.user:
        raise Http404
    status_updates = emergency.status_updates.all()
    allowed = emergency.allowed_transitions(request.user)
    return render(request, 'emergencies/emergency_detail.html', {
        'emergency':      emergency,
        'status_updates': status_updates,
        'allowed':        allowed,
    })


@login_required
def update_status(request, pk):
    emergency = get_object_or_404(EmergencyRequest, pk=pk)
    allowed = emergency.allowed_transitions(request.user)
    if not allowed:
        messages.error(request, "You don't have permission to update this status.")
        return redirect('emergencies:emergency_detail', pk=pk)
    if request.method == 'POST':
        form = StatusUpdateForm(request.POST, allowed_transitions=allowed)
        if form.is_valid():
            new_status = form.cleaned_data['new_status']
            valid_values = [v for v, _ in allowed]
            if new_status not in valid_values:
                messages.error(request, 'Invalid status transition.')
                return redirect('emergencies:emergency_detail', pk=pk)
            StatusUpdate.objects.create(
                emergency=emergency,
                changed_by=request.user,
                from_status=emergency.status,
                to_status=new_status,
                notes=form.cleaned_data['notes'],
            )
            emergency.status = new_status
            emergency.last_status_change = timezone.now()
            emergency.save()
            messages.success(request, f"Status updated to '{new_status}'.")
            return redirect('emergencies:emergency_detail', pk=pk)
    else:
        form = StatusUpdateForm(allowed_transitions=allowed)
    return render(request, 'emergencies/update_status.html', {
        'emergency': emergency,
        'form':      form,
    })


@staff_member_required
def admin_job_dashboard(request):
    emergencies = EmergencyRequest.objects.select_related(
        'vessel', 'submitted_by', 'assigned_provider'
    ).order_by('-created_at')
    for e in emergencies:
        e.colour  = e.dashboard_colour()
        e.elapsed = e.minutes_since_last_change()
    total          = emergencies.count()
    active_count   = emergencies.filter(status='active').count()
    reported_count = emergencies.filter(status='reported').count()
    resolved_count = emergencies.filter(status='resolved').count()
    approved_providers = RecoveryProvider.objects.filter(
        verification_status='approved'
    ).order_by('company_name')
    return render(request, 'emergencies/admin_job_dashboard.html', {
        'emergencies':        emergencies,
        'total':              total,
        'active_count':       active_count,
        'reported_count':     reported_count,
        'resolved_count':     resolved_count,
        'approved_providers': approved_providers,
    })


@staff_member_required
def admin_assign_provider(request, pk):
    emergency = get_object_or_404(EmergencyRequest, pk=pk)
    if request.method == 'POST':
        provider_id = request.POST.get('provider_id')
        if not provider_id:
            messages.error(request, 'Please select a provider.')
            return redirect('emergencies:admin_job_dashboard')
        provider = get_object_or_404(
            RecoveryProvider, pk=provider_id, verification_status='approved'
        )
        old_status = emergency.status
        emergency.assigned_provider = provider
        emergency.status = 'active'
        emergency.last_status_change = timezone.now()
        emergency.save()
        StatusUpdate.objects.create(
            emergency=emergency,
            changed_by=request.user,
            from_status=old_status,
            to_status='active',
            notes=f'Manually assigned to {provider.company_name} by admin.',
        )
        messages.success(request, f'Emergency #{pk} assigned to {provider.company_name}.')
    return redirect('emergencies:admin_job_dashboard')


@staff_member_required
def admin_escalate(request, pk):
    emergency = get_object_or_404(EmergencyRequest, pk=pk)
    if request.method == 'POST':
        reason = request.POST.get('reason', 'Escalated to coastguard by admin.')
        old_status = emergency.status
        StatusUpdate.objects.create(
            emergency=emergency,
            changed_by=request.user,
            from_status=old_status,
            to_status='cancelled',
            notes=f'ESCALATED: {reason} - Contact coastguard on 999 or 112.',
        )
        emergency.status = 'cancelled'
        emergency.last_status_change = timezone.now()
        emergency.save()
        messages.warning(
            request,
            f'Emergency #{pk} escalated to coastguard. Vessel operator should call 999/112.'
        )
    return redirect('emergencies:admin_job_dashboard')