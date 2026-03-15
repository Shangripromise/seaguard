from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Vessel
from .forms import VesselForm


@login_required
def vessel_list(request):
    vessels = Vessel.objects.filter(owner=request.user)
    return render(request, 'vessels/vessel_list.html', {'vessels': vessels})


@login_required
def vessel_add(request):
    if request.method == 'POST':
        form = VesselForm(request.POST)
        if form.is_valid():
            vessel = form.save(commit=False)
            vessel.owner = request.user
            vessel.save()
            messages.success(request, 'Vessel added successfully!')
            return redirect('vessel_list')
    else:
        form = VesselForm()
    return render(request, 'vessels/vessel_add.html', {'form': form})


@login_required
def vessel_detail(request, pk):
    vessel = get_object_or_404(Vessel, pk=pk, owner=request.user)
    return render(request, 'vessels/vessel_detail.html', {'vessel': vessel})


@login_required
def vessel_delete(request, pk):
    vessel = get_object_or_404(Vessel, pk=pk, owner=request.user)
    if request.method == 'POST':
        vessel.delete()
        messages.success(request, 'Vessel deleted.')
        return redirect('vessel_list')
    return render(request, 'vessels/vessel_confirm_delete.html', {'vessel': vessel})

