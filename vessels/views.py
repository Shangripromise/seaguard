from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Vessel, VesselDocument, MaintenanceRequest, PassagePlan
from .forms import VesselForm, VesselDocumentForm, MaintenanceRequestForm, PassagePlanForm

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
            return redirect('vessels:vessel_list')
    else:
        form = VesselForm()
    return render(request, 'vessels/vessel_add.html', {'form': form})

@login_required
def vessel_detail(request, pk):
    vessel = get_object_or_404(Vessel, pk=pk, owner=request.user)
    documents = vessel.documents.all().order_by('-uploaded_at')
    maintenance_requests = vessel.maintenance_requests.all().order_by('-created_at')
    passage_plans = vessel.passage_plans.all().order_by('-created_at')
    return render(request, 'vessels/vessel_detail.html', {
        'vessel': vessel,
        'documents': documents,
        'maintenance_requests': maintenance_requests,
        'passage_plans': passage_plans,
    })

@login_required
def vessel_delete(request, pk):
    vessel = get_object_or_404(Vessel, pk=pk, owner=request.user)
    if request.method == 'POST':
        vessel.delete()
        messages.success(request, 'Vessel deleted.')
        return redirect('vessels:vessel_list')
    return render(request, 'vessels/vessel_confirm_delete.html', {'vessel': vessel})

@login_required
def document_upload(request, vessel_pk):
    vessel = get_object_or_404(Vessel, pk=vessel_pk, owner=request.user)
    if request.method == 'POST':
        form = VesselDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.vessel = vessel
            doc.save()
            messages.success(request, 'Document uploaded successfully.')
            return redirect('vessels:vessel_detail', pk=vessel_pk)
    else:
        form = VesselDocumentForm()
    return render(request, 'vessels/document_upload.html', {'form': form, 'vessel': vessel})

@login_required
def document_delete(request, pk):
    doc = get_object_or_404(VesselDocument, pk=pk, vessel__owner=request.user)
    vessel_pk = doc.vessel.pk
    if request.method == 'POST':
        doc.file.delete(save=False)
        doc.delete()
        messages.success(request, 'Document deleted.')
        return redirect('vessels:vessel_detail', pk=vessel_pk)
    return render(request, 'vessels/document_confirm_delete.html', {'doc': doc})

@login_required
def maintenance_request(request, vessel_pk):
    vessel = get_object_or_404(Vessel, pk=vessel_pk, owner=request.user)
    if request.method == 'POST':
        form = MaintenanceRequestForm(request.POST)
        if form.is_valid():
            req = form.save(commit=False)
            req.vessel = vessel
            req.save()
            messages.success(request, 'Maintenance request submitted. An approved contractor will be in touch.')
            return redirect('vessels:vessel_detail', pk=vessel_pk)
    else:
        form = MaintenanceRequestForm()
    return render(request, 'vessels/maintenance_request.html', {'form': form, 'vessel': vessel})

@login_required
def maintenance_detail(request, pk):
    req = get_object_or_404(MaintenanceRequest, pk=pk, vessel__owner=request.user)
    return render(request, 'vessels/maintenance_detail.html', {'req': req})

@login_required
def passage_plan_create(request, vessel_pk):
    vessel = get_object_or_404(Vessel, pk=vessel_pk, owner=request.user)
    if request.method == 'POST':
        form = PassagePlanForm(request.POST)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.vessel = vessel
            plan.save()
            messages.success(request, 'Passage plan created.')
            return redirect('vessels:vessel_detail', pk=vessel_pk)
    else:
        form = PassagePlanForm()
    return render(request, 'vessels/passage_plan_form.html', {'form': form, 'vessel': vessel, 'action': 'Create'})

@login_required
def passage_plan_detail(request, pk):
    plan = get_object_or_404(PassagePlan, pk=pk, vessel__owner=request.user)
    return render(request, 'vessels/passage_plan_detail.html', {'plan': plan})

@login_required
def passage_plan_edit(request, pk):
    plan = get_object_or_404(PassagePlan, pk=pk, vessel__owner=request.user)
    if request.method == 'POST':
        form = PassagePlanForm(request.POST, instance=plan)
        if form.is_valid():
            form.save()
            messages.success(request, 'Passage plan updated.')
            return redirect('vessels:passage_plan_detail', pk=pk)
    else:
        form = PassagePlanForm(instance=plan)
    return render(request, 'vessels/passage_plan_form.html', {'form': form, 'vessel': plan.vessel, 'action': 'Edit'})

@login_required
def passage_plan_delete(request, pk):
    plan = get_object_or_404(PassagePlan, pk=pk, vessel__owner=request.user)
    vessel_pk = plan.vessel.pk
    if request.method == 'POST':
        plan.delete()
        messages.success(request, 'Passage plan deleted.')
        return redirect('vessels:vessel_detail', pk=vessel_pk)
    return render(request, 'vessels/passage_plan_confirm_delete.html', {'plan': plan})
