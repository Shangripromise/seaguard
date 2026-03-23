from django.db import models
from django.contrib.auth.models import User


class Vessel(models.Model):
    VESSEL_TYPES = [
        ('sailing', 'Sailing Yacht'),
        ('motor', 'Motor Yacht'),
        ('catamaran', 'Catamaran'),
        ('rib', 'RIB / Inflatable'),
        ('cargo', 'Cargo Ship'),
        ('tanker', 'Tanker'),
        ('passenger', 'Passenger Ship'),
        ('fishing', 'Fishing Vessel'),
        ('tug', 'Tug Boat'),
        ('other', 'Other'),
    ]
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vessels')
    name = models.CharField(max_length=100)
    imo_number = models.CharField(max_length=20, unique=True)
    vessel_type = models.CharField(max_length=20, choices=VESSEL_TYPES)
    flag = models.CharField(max_length=50)
    call_sign = models.CharField(max_length=20, blank=True)
    mmsi = models.CharField(max_length=20, blank=True, verbose_name='MMSI')
    ssr_number = models.CharField(max_length=30, blank=True, verbose_name='SSR Number')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.name} ({self.imo_number})'


class VesselDocument(models.Model):
    DOCUMENT_TYPES = [
        ('insurance', 'Insurance Certificate'),
        ('registration', 'Registration / SSR Certificate'),
        ('safety', 'Safety Equipment Checklist'),
        ('passage_plan', 'Passage Plan / Float Plan'),
        ('other', 'Other'),
    ]
    vessel = models.ForeignKey(Vessel, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPES)
    title = models.CharField(max_length=100)
    file = models.FileField(upload_to='vessel_documents/')
    expiry_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.vessel.name} — {self.get_document_type_display()}'


class MaintenanceRequest(models.Model):
    STATUS_CHOICES = [
        ('requested', 'Requested'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    CHECK_TYPES = [
        ('pre_passage', 'Pre-Passage Safety Check'),
        ('annual', 'Annual Service'),
        ('engine', 'Engine Service'),
        ('rigging', 'Rigging Inspection'),
        ('electrical', 'Electrical Systems'),
        ('hull', 'Hull Inspection'),
        ('safety_equipment', 'Safety Equipment Check'),
        ('other', 'Other'),
    ]
    vessel = models.ForeignKey(Vessel, on_delete=models.CASCADE, related_name='maintenance_requests')
    check_type = models.CharField(max_length=30, choices=CHECK_TYPES)
    description = models.TextField(help_text='Describe what needs checking or any known issues')
    requested_date = models.DateField(help_text='When do you need this completed by?')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')
    assigned_contractor = models.CharField(max_length=100, blank=True)
    contractor_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.vessel.name} — {self.get_check_type_display()}'


class PassagePlan(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('filed', 'Filed'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    vessel = models.ForeignKey(Vessel, on_delete=models.CASCADE, related_name='passage_plans')
    title = models.CharField(max_length=100, help_text='e.g. Cowes to Cherbourg')
    departure_port = models.CharField(max_length=100)
    destination_port = models.CharField(max_length=100)
    departure_datetime = models.DateTimeField()
    estimated_arrival = models.DateTimeField(null=True, blank=True)

    # Route planning
    route_description = models.TextField(help_text='Waypoints, headings, distances')
    hazards = models.TextField(blank=True, help_text='Rocks, shoals, traffic separation schemes')
    alternate_ports = models.TextField(blank=True, help_text='Ports of refuge along the route')
    vhf_channels = models.CharField(max_length=100, blank=True, help_text='e.g. Ch16, Ch67, Ch80')
    tidal_notes = models.TextField(blank=True, help_text='Tidal windows, heights, streams')
    current_notes = models.TextField(blank=True)

    # Crew
    crew_list = models.TextField(blank=True, help_text='Names and roles of all persons on board')
    persons_on_board = models.PositiveIntegerField(default=1)

    # Pre-departure checks
    check_bilge = models.BooleanField(default=False, verbose_name='Bilge checked')
    check_engine_bilge = models.BooleanField(default=False, verbose_name='Engine bilge checked')
    check_oil_level = models.BooleanField(default=False, verbose_name='Oil level checked')
    check_coolant = models.BooleanField(default=False, verbose_name='Coolant level checked')
    check_transmission = models.BooleanField(default=False, verbose_name='Transmission belt checked')
    engine_battery_v = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, verbose_name='Engine battery (V)')
    service_battery_v = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, verbose_name='Service battery (V)')
    fuel_level_pct = models.PositiveIntegerField(null=True, blank=True, verbose_name='Fuel level (%)')
    water_fwd_pct = models.PositiveIntegerField(null=True, blank=True, verbose_name='Fwd water tank (%)')
    water_aft_pct = models.PositiveIntegerField(null=True, blank=True, verbose_name='Aft water tank (%)')

    # Engine hours
    engine_hours_start = models.DecimalField(max_digits=8, decimal_places=1, null=True, blank=True)
    engine_hours_end = models.DecimalField(max_digits=8, decimal_places=1, null=True, blank=True)

    # Weather
    weather_forecast = models.TextField(blank=True)
    sea_state = models.CharField(max_length=50, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.vessel.name} — {self.title}'