from django.urls import path
from users.id_encryption import register_eid_converter
from . import views

register_eid_converter()

app_name = 'evaluations'

urlpatterns = [
    # Admin routes
    path('', views.evaluation_list, name='evaluation_list'),
    path('create/', views.evaluation_create, name='evaluation_create'),
    path('<eid:pk>/', views.evaluation_detail, name='evaluation_detail'),
    path('templates/', views.template_list, name='template_list'),
    path('templates/create/', views.template_create, name='template_create'),
    path('templates/<eid:pk>/edit/', views.template_edit, name='template_edit'),
    path('units/', views.unit_list, name='unit_list'),
    path('units/create/', views.unit_create, name='unit_create'),
    path('units/<eid:pk>/', views.unit_detail, name='unit_detail'),
    path('units/<eid:pk>/edit/', views.unit_edit, name='unit_edit'),
    path('submissions/', views.admin_submissions_list, name='admin_submissions_list'),
    path('submissions/<eid:pk>/', views.admin_submission_detail, name='admin_submission_detail'),
    path('submissions/evaluation/<eid:evaluation_id>/user/<eid:user_id>/', views.admin_user_received_reviews, name='admin_user_received_reviews'),
    path('<eid:pk>/matrix/', views.evaluation_matrix, name='evaluation_matrix'),

    # User (Employee) routes
    path('my/', views.user_evaluations, name='user_evaluations'),
    path('<eid:pk>/rate/<eid:evaluatee_id>/', views.evaluation_rate, name='evaluation_rate'),
    path('my-history/', views.user_history, name='user_history'),
    path('my-history/<eid:pk>/', views.user_history_detail, name='user_history_detail'),
]
