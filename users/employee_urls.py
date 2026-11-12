from django.urls import path
from .id_encryption import register_eid_converter
from . import views

register_eid_converter()

app_name = 'employees'

urlpatterns = [
    path('', views.employee_list, name='list'),
    path('audit/', views.audit_log_view, name='audit_log'),
    path('create/', views.employee_create, name='create'),
    path('<eid:pk>/edit/', views.employee_edit, name='edit'),
    path('<eid:pk>/reset-password/', views.employee_reset_password, name='reset_password'),
]
