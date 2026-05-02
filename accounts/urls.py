from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/',                views.register_view,        name='register'),
    path('login/',                   views.login_view,           name='login'),
    path('logout/',                  views.logout_view,          name='logout'),
    path('dashboard/',               views.dashboard_view,       name='dashboard'),
    path('admin-dashboard/',         views.admin_dashboard,      name='admin_dashboard'),
    path('discounts/',               views.member_discounts,     name='member_discounts'),

    # CR6 — Voucher Service
    path('vouchers/redeem/',         views.redeem_voucher,       name='redeem_voucher'),
    path('vouchers/manage/',         views.admin_voucher_list,   name='admin_voucher_list'),
    path('vouchers/manage/create/',  views.admin_voucher_create, name='admin_voucher_create'),

    # CR7 — Bulk Data Ingestion
    path('ingest/',                  views.bulk_ingest,          name='bulk_ingest'),
]