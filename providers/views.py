from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import Http404

from .forms import RecoveryProviderRegistrationForm, ProviderRatingForm
from .models import RecoveryProvider, ProviderRating


def is_staff(user):
    return user.is_staff


def provider_register(request):
    if request.user.is_authenticated:
        return redirect('providers:dashboard')

    if request.method == 'POST':
        form = RecoveryProviderRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration submitted! Your account is pending verification.')
            return redirect('providers:pending_approval')
    else:
        form = RecoveryProviderRegistrationForm()

    return render(request, 'providers/register.html', {'form': form})


def provider_list(request):
    providers = RecoveryProvider.objects.filter(
        verification_status='approved'
    ).select_related('user').order_by('company_name')
    return render(request, 'providers/provider_list.html', {'providers': providers})


def provider_detail(request, provider_id):
    provider = get_object_or_404(RecoveryProvider, pk=provider_id, verification_status='approved')
    ratings = provider.ratings.select_related('rated_by').all()

    user_rating = None
    if request.user.is_authenticated:
        user_rating = ProviderRating.objects.filter(
            provider=provider, rated_by=request.user
        ).first()

    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, 'You must be logged in to leave a rating.')
            return redirect('login')

        if user_rating:
            form = ProviderRatingForm(request.POST, instance=user_rating)
        else:
            form = ProviderRatingForm(request.POST)

        if form.is_valid():
            rating = form.save(commit=False)
            rating.provider = provider
            rating.rated_by = request.user
            rating.save()
            messages.success(request, 'Your rating has been saved.')
            return redirect('providers:detail', provider_id=provider.pk)
    else:
        form = ProviderRatingForm(instance=user_rating) if user_rating else ProviderRatingForm()

    return render(request, 'providers/provider_detail.html', {
        'provider':    provider,
        'ratings':     ratings,
        'user_rating': user_rating,
        'form':        form,
    })


@login_required
def pending_approval(request):
    try:
        provider = request.user.provider_profile
    except RecoveryProvider.DoesNotExist:
        raise Http404
    if provider.verification_status == 'approved':
        return redirect('providers:dashboard')
    if provider.verification_status == 'rejected':
        return render(request, 'providers/rejected.html', {'provider': provider})
    return render(request, 'providers/pending_approval.html', {'provider': provider})


@login_required
def provider_dashboard(request):
    try:
        provider = request.user.provider_profile
    except RecoveryProvider.DoesNotExist:
        raise Http404
    if provider.verification_status != 'approved':
        return redirect('providers:pending_approval')
    ratings = provider.ratings.select_related('rated_by').all()
    return render(request, 'providers/dashboard.html', {
        'provider': provider,
        'ratings':  ratings,
    })


@login_required
@user_passes_test(is_staff)
def admin_provider_review(request):
    pending  = RecoveryProvider.objects.filter(verification_status='pending').select_related('user')
    approved = RecoveryProvider.objects.filter(verification_status='approved').select_related('user')
    rejected = RecoveryProvider.objects.filter(verification_status='rejected').select_related('user')
    return render(request, 'providers/admin_review.html', {
        'pending':  pending,
        'approved': approved,
        'rejected': rejected,
    })


@login_required
@user_passes_test(is_staff)
def admin_provider_approve(request, provider_id):
    provider = get_object_or_404(RecoveryProvider, pk=provider_id)
    if request.method == 'POST':
        provider.verification_status = 'approved'
        provider.save()
        messages.success(request, f'{provider.company_name} has been approved.')
    return redirect('providers:admin_review')


@login_required
@user_passes_test(is_staff)
def admin_provider_reject(request, provider_id):
    provider = get_object_or_404(RecoveryProvider, pk=provider_id)
    if request.method == 'POST':
        provider.verification_status = 'rejected'
        provider.save()
        messages.warning(request, f'{provider.company_name} has been rejected.')
    return redirect('providers:admin_review')