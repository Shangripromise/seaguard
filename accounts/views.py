import csv
import json
import io
import uuid

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone

from .forms import RegisterForm, LoginForm
from .models import Voucher, VoucherRedemption
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
            return redirect('accounts:dashboard')
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
            return redirect('accounts:dashboard')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('accounts:login')


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
    total_users          = User.objects.count()
    total_vessels        = Vessel.objects.count()
    total_emergencies    = EmergencyRequest.objects.count()
    active_emergencies   = EmergencyRequest.objects.filter(
        status='active'
    ).select_related('vessel', 'assigned_provider')
    reported_emergencies = EmergencyRequest.objects.filter(
        status='reported'
    ).select_related('vessel')
    pending_ratings   = ProviderRating.objects.filter(
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
    CR3 — Member Discounts / Promotional Placement page.
    FR-VO-DISC-001: accessible to authenticated vessel operators.
    FR-VO-DISC-002: blocked during any active emergency request.
    """
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

    discounts = [
        {
            'partner':     'Berthon Boat Co.',
            'category':    'Marine Services',
            'offer':       '10% off annual vessel servicing',
            'code':        'SEAGUARD10',
            'valid_until': 'Dec 2026',
        },
        {
            'partner':     'Pantaenius UK',
            'category':    'Marine Insurance',
            'offer':       '15% discount on new yacht insurance policies',
            'code':        'SG-PANT15',
            'valid_until': 'Jun 2026',
        },
        {
            'partner':     'Force 4 Chandlery',
            'category':    'Marine Equipment',
            'offer':       '12% off safety equipment orders over £100',
            'code':        'SGFORCE12',
            'valid_until': 'Dec 2026',
        },
        {
            'partner':     'RYA Training',
            'category':    'Training & Certification',
            'offer':       '£50 off any RYA practical course',
            'code':        'SGRYATRN',
            'valid_until': 'Sep 2026',
        },
        {
            'partner':     'Fuel Marine',
            'category':    'Fuel & Lubricants',
            'offer':       '8p per litre discount on marina fuel',
            'code':        'SGFUEL8',
            'valid_until': 'Dec 2026',
        },
    ]

    return render(request, 'accounts/member_discounts.html', {
        'discounts': discounts,
    })


# ── CR6: Voucher Service ──────────────────────────────────────────────────────

@login_required
def redeem_voucher(request):
    """
    CR6 — Voucher redemption.
    FR-VO-VOUC-001: member can enter a voucher code to claim a discount.
    FR-VO-VOUC-002: system validates code, expiry, max uses, and prevents
                    double redemption by the same member.
    """
    redemption = None
    voucher = None

    if request.method == 'POST':
        code = request.POST.get('code', '').strip().upper()
        try:
            voucher = Voucher.objects.get(code=code)
        except Voucher.DoesNotExist:
            messages.error(request, f'Voucher code "{code}" does not exist.')
        else:
            if VoucherRedemption.objects.filter(
                    voucher=voucher, redeemed_by=request.user).exists():
                messages.error(request, 'You have already redeemed this voucher.')
                voucher = None
            else:
                valid, reason = voucher.is_valid()
                if not valid:
                    messages.error(request, reason)
                    voucher = None
                else:
                    redemption = VoucherRedemption.objects.create(
                        voucher=voucher,
                        redeemed_by=request.user,
                        applied_to=voucher.applies_to,
                    )
                    messages.success(
                        request,
                        f'Voucher "{voucher.code}" redeemed successfully! '
                        f'{voucher.get_discount_type_display()}: '
                        f'{voucher.discount_value} off '
                        f'{voucher.get_applies_to_display()}.'
                    )

    my_redemptions = VoucherRedemption.objects.filter(
        redeemed_by=request.user
    ).select_related('voucher').order_by('-redeemed_at')

    return render(request, 'accounts/redeem_voucher.html', {
        'redemption':     redemption,
        'voucher':        voucher,
        'my_redemptions': my_redemptions,
    })


@login_required
def admin_voucher_list(request):
    """
    CR6 — Admin voucher monitoring dashboard.
    FR-SA-VOUC-001: staff can view all vouchers, usage counts, redemption log.
    """
    if not request.user.is_staff:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')

    vouchers = Voucher.objects.prefetch_related('redemptions').order_by('-created_at')
    return render(request, 'accounts/admin_voucher_list.html', {
        'vouchers': vouchers,
    })


@login_required
def admin_voucher_create(request):
    """
    CR6 — Admin creates a new voucher code.
    FR-SA-VOUC-002: staff can create vouchers with type, value, expiry, max uses.
    """
    if not request.user.is_staff:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        code           = request.POST.get('code', '').strip().upper()
        description    = request.POST.get('description', '').strip()
        discount_type  = request.POST.get('discount_type', 'percentage')
        discount_value = request.POST.get('discount_value', '0')
        applies_to     = request.POST.get('applies_to', 'general')
        expiry_date    = request.POST.get('expiry_date') or None
        max_uses_raw   = request.POST.get('max_uses') or None
        is_active      = request.POST.get('is_active') == 'on'

        if not code:
            messages.error(request, 'Voucher code cannot be empty.')
        elif Voucher.objects.filter(code=code).exists():
            messages.error(request, f'Voucher code "{code}" already exists.')
        else:
            Voucher.objects.create(
                code=code,
                description=description,
                discount_type=discount_type,
                discount_value=discount_value,
                applies_to=applies_to,
                expiry_date=expiry_date,
                max_uses=int(max_uses_raw) if max_uses_raw else None,
                is_active=is_active,
                created_by=request.user,
            )
            messages.success(request, f'Voucher "{code}" created successfully.')
            return redirect('accounts:admin_voucher_list')

    return render(request, 'accounts/admin_voucher_create.html', {
        'discount_types':     Voucher.DISCOUNT_TYPE_CHOICES,
        'applies_to_choices': Voucher.APPLIES_TO_CHOICES,
    })


# ── CR7: Bulk Data Ingestion ──────────────────────────────────────────────────

@login_required
def bulk_ingest(request):
    """
    CR7 — CSV/JSON bulk data ingestion without creating duplicates.
    FR-SA-ING-001: admin uploads CSV or JSON file.
    FR-SA-ING-002: system detects data type from headers automatically.
    FR-SA-ING-003: duplicate records are skipped, not inserted.
    FR-SA-ING-004: ingestion summary shown to admin.
    """
    if not request.user.is_staff:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')

    results = None

    if request.method == 'POST' and request.FILES.get('datafile'):
        uploaded = request.FILES['datafile']
        filename = uploaded.name.lower()

        try:
            if filename.endswith('.csv'):
                decoded = uploaded.read().decode('utf-8')
                reader  = csv.DictReader(io.StringIO(decoded))
                records = list(reader)
            elif filename.endswith('.json'):
                decoded = uploaded.read().decode('utf-8')
                records = json.loads(decoded)
                if isinstance(records, dict):
                    records = [records]
            else:
                messages.error(
                    request,
                    'Unsupported file type. Please upload a .csv or .json file.'
                )
                return render(request, 'accounts/bulk_ingest.html', {'results': None})

            if not records:
                messages.warning(request, 'The file contained no records.')
                return render(request, 'accounts/bulk_ingest.html', {'results': None})

            # Auto-detect data type from headers
            headers = set(records[0].keys())

            if 'imo_number' in headers:
                results = _ingest_vessels(records, request.user)
            elif 'company_name' in headers:
                results = _ingest_providers(records)
            else:
                messages.error(
                    request,
                    'Could not detect data type. File must contain "imo_number" '
                    '(vessels) or "company_name" (providers) as a column header.'
                )
                return render(request, 'accounts/bulk_ingest.html', {'results': None})

        except Exception as e:
            messages.error(request, f'Error processing file: {e}')
            return render(request, 'accounts/bulk_ingest.html', {'results': None})

    return render(request, 'accounts/bulk_ingest.html', {'results': results})


def _ingest_vessels(records, user):
    """Process vessel records — skip duplicates on imo_number."""
    created = []
    skipped = []
    errors  = []

    for i, row in enumerate(records, start=1):
        imo  = row.get('imo_number', '').strip()
        name = row.get('name', '').strip()

        if not imo or not name:
            errors.append(f'Row {i}: missing required fields (name, imo_number).')
            continue

        if Vessel.objects.filter(imo_number=imo).exists():
            skipped.append(f'{name} ({imo}) — duplicate IMO number.')
        else:
            try:
                Vessel.objects.create(
                    owner=user,
                    name=name,
                    imo_number=imo,
                    vessel_type=row.get('vessel_type', 'other'),
                    flag=row.get('flag', 'Unknown'),
                    call_sign=row.get('call_sign', ''),
                    mmsi=row.get('mmsi', ''),
                    description=row.get('description', ''),
                )
                created.append(f'{name} ({imo})')
            except Exception as e:
                errors.append(f'Row {i} ({name}): {e}')

    return {
        'data_type': 'Vessels',
        'total':     len(records),
        'created':   created,
        'skipped':   skipped,
        'errors':    errors,
    }


def _ingest_providers(records):
    """
    Process provider records — skip duplicates on company_name.
    Each provider gets a unique placeholder user account since
    RecoveryProvider has a OneToOne relationship with User.
    """
    created = []
    skipped = []
    errors  = []

    for i, row in enumerate(records, start=1):
        company = row.get('company_name', '').strip()

        if not company:
            errors.append(f'Row {i}: missing required field (company_name).')
            continue

        if RecoveryProvider.objects.filter(company_name=company).exists():
            skipped.append(f'{company} — duplicate company name.')
        else:
            try:
                # Generate a unique placeholder user for each bulk-imported provider
                placeholder_username = (
                    f"provider_{company[:20].lower().replace(' ', '_')}"
                    f"_{uuid.uuid4().hex[:6]}"
                )
                placeholder_user = User.objects.create_user(
                    username=placeholder_username,
                    password=uuid.uuid4().hex,
                )
                RecoveryProvider.objects.create(
                    user=placeholder_user,
                    company_name=company,
                    contact_person=row.get('contact_person', ''),
                    business_registration=row.get('business_registration', 'N/A'),
                    phone_number=row.get('phone_number', ''),
                    service_type=row.get('service_type', 'general'),
                    service_area=row.get('service_area', ''),
                    verification_status='pending',
                )
                created.append(f'{company}')
            except Exception as e:
                errors.append(f'Row {i} ({company}): {e}')

    return {
        'data_type': 'Recovery Providers',
        'total':     len(records),
        'created':   created,
        'skipped':   skipped,
        'errors':    errors,
    }