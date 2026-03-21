from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Q
from django.http import Http404
from django.utils import timezone

from .forms import RecoveryProviderRegistrationForm, ProviderRatingForm
from .models import RecoveryProvider, ProviderRating


def is_staff(user):
    return user.is_staff


# ---------------------------------------------------------------------------
# Existing views — unchanged logic, preserved exactly
# ---------------------------------------------------------------------------

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
    provider = get_object_or_404(RecoveryProvider, pk=provider_id,
                                 verification_status='approved')
    # CR4 — only show approved ratings publicly
    ratings = provider.ratings.filter(
        moderation_status='approved'
    ).select_related('rated_by')

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
            # CR4 — new/updated ratings go back to pending moderation
            rating.moderation_status = 'pending'
            rating.rejection_reason  = ''
            rating.moderated_by      = None
            rating.moderated_at      = None
            rating.save()
            messages.success(request, 'Your rating has been submitted for review.')
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
    ratings = provider.ratings.filter(
        moderation_status='approved'
    ).select_related('rated_by')
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


# ---------------------------------------------------------------------------
# CR1 — Advanced search / filter on provider directory
# FR-VO-SEA-001 / FR-VO-SEA-002
# ---------------------------------------------------------------------------

def provider_search(request):
    """
    Keyword search across company_name and service_area,
    with availability status filter.
    """
    query        = request.GET.get('q', '').strip()
    availability = request.GET.get('availability', '')

    providers = RecoveryProvider.objects.filter(
        verification_status='approved'
    ).select_related('user')

    if query:
        providers = providers.filter(
            Q(company_name__icontains=query) |
            Q(service_area__icontains=query) |
            Q(service_type__icontains=query)
        )

    if availability == 'available':
        providers = providers.filter(is_available=True)
    elif availability == 'unavailable':
        providers = providers.filter(is_available=False)

    providers = providers.order_by('company_name')

    return render(request, 'providers/provider_search.html', {
        'providers':    providers,
        'query':        query,
        'availability': availability,
    })


# ---------------------------------------------------------------------------
# CR4 — Admin rating moderation queue
# FR-SA-MOD-001 / FR-SA-MOD-002 / FR-SA-MOD-003
# ---------------------------------------------------------------------------

@staff_member_required
def admin_rating_moderation(request):
    """
    FR-SA-MOD-001 — Moderation queue showing all pending ratings.
    """
    pending  = ProviderRating.objects.filter(
                   moderation_status='pending'
               ).select_related('provider', 'rated_by').order_by('created_at')
    approved = ProviderRating.objects.filter(
                   moderation_status='approved'
               ).select_related('provider', 'rated_by').order_by('-moderated_at')
    rejected = ProviderRating.objects.filter(
                   moderation_status='rejected'
               ).select_related('provider', 'rated_by').order_by('-moderated_at')

    return render(request, 'providers/admin_rating_moderation.html', {
        'pending':  pending,
        'approved': approved,
        'rejected': rejected,
        'rejection_reasons': ProviderRating.REJECTION_REASONS,
    })


@staff_member_required
def admin_rating_approve(request, rating_id):
    """
    FR-SA-MOD-002 — Approve a pending rating; makes it publicly visible.
    """
    rating = get_object_or_404(ProviderRating, pk=rating_id)
    if request.method == 'POST':
        rating.moderation_status = 'approved'
        rating.moderated_by      = request.user
        rating.moderated_at      = timezone.now()
        rating.rejection_reason  = ''
        rating.save()
        messages.success(
            request,
            f'Rating by {rating.rated_by.username} for '
            f'{rating.provider.company_name} approved.'
        )
    return redirect('providers:admin_rating_moderation')


@staff_member_required
def admin_rating_reject(request, rating_id):
    """
    FR-SA-MOD-003 — Reject a pending rating with a documented reason.
    """
    rating = get_object_or_404(ProviderRating, pk=rating_id)
    if request.method == 'POST':
        reason = request.POST.get('rejection_reason', 'other')
        valid_reasons = [r[0] for r in ProviderRating.REJECTION_REASONS]
        if reason not in valid_reasons:
            reason = 'other'
        rating.moderation_status = 'rejected'
        rating.rejection_reason  = reason
        rating.moderated_by      = request.user
        rating.moderated_at      = timezone.now()
        rating.save()
        messages.warning(
            request,
            f'Rating by {rating.rated_by.username} rejected: {reason}.'
        )
    return redirect('providers:admin_rating_moderation')