from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import EmergencyRequest, StatusUpdate
from .forms import EmergencyRequestForm, StatusUpdateForm


@login_required
def emergency_list(request):
    emergencies = EmergencyRequest.objects.filter(submitted_by=request.user)
    return render(request, 'emergencies/emergency_list.html', {'emergencies': emergencies})


@login_required
def emergency_submit(request):
    if request.method == 'POST':
        form = EmergencyRequestForm(request.user, request.POST)
        if form.is_valid():
            emergency = form.save(commit=False)
            emergency.submitted_by = request.user
            emergency.save()
            messages.success(request, 'Emergency request submitted!')
            return redirect('emergencies:emergency_list')
    else:
        form = EmergencyRequestForm(request.user)
    return render(request, 'emergencies/emergency_submit.html', {'form': form})


@login_required
def emergency_detail(request, pk):
    emergency = get_object_or_404(EmergencyRequest, pk=pk)
    status_updates = emergency.status_updates.all()
    allowed = emergency.allowed_transitions(request.user)
    return render(request, 'emergencies/emergency_detail.html', {
        'emergency': emergency,
        'status_updates': status_updates,
        'allowed': allowed,
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
            emergency.save()
            messages.success(request, f"Status updated to '{new_status}'.")
            return redirect('emergencies:emergency_detail', pk=pk)
    else:
        form = StatusUpdateForm(allowed_transitions=allowed)

    return render(request, 'emergencies/update_status.html', {
        'emergency': emergency,
        'form': form,
    })