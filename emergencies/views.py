from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import EmergencyRequest
from .forms import EmergencyRequestForm


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
            return redirect('emergency_list')
    else:
        form = EmergencyRequestForm(request.user)
    return render(request, 'emergencies/emergency_submit.html', {'form': form})


@login_required
def emergency_detail(request, pk):
    emergency = get_object_or_404(EmergencyRequest, pk=pk, submitted_by=request.user)
    return render(request, 'emergencies/emergency_detail.html', {'emergency': emergency})