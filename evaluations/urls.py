from django.urls import path
from . import views

app_name = 'evaluations'

urlpatterns = [
    # Admin routes
    path('', views.evaluation_list, name='evaluation_list'),
    path('create/', views.evaluation_create, name='evaluation_create'),
    path('<int:pk>/', views.evaluation_detail, name='evaluation_detail'),
    path('templates/', views.template_list, name='template_list'),
    path('templates/create/', views.template_create, name='template_create'),
    path('templates/<int:pk>/edit/', views.template_edit, name='template_edit'),
    path('units/', views.unit_list, name='unit_list'),
    path('units/create/', views.unit_create, name='unit_create'),
    path('units/<int:pk>/', views.unit_detail, name='unit_detail'),
    path('units/<int:pk>/edit/', views.unit_edit, name='unit_edit'),
    path('submissions/', views.admin_submissions_list, name='admin_submissions_list'),
    path('submissions/<int:pk>/', views.admin_submission_detail, name='admin_submission_detail'),
    path('submissions/evaluation/<int:evaluation_id>/user/<int:user_id>/', views.admin_user_received_reviews, name='admin_user_received_reviews'),
    path('<int:pk>/matrix/', views.evaluation_matrix, name='evaluation_matrix'),

    # User (Employee) routes
    path('my/', views.user_evaluations, name='user_evaluations'),
    path('<int:pk>/rate/<int:evaluatee_id>/', views.evaluation_rate, name='evaluation_rate'),
    path('my-history/', views.user_history, name='user_history'),
    path('my-history/<int:pk>/', views.user_history_detail, name='user_history_detail'),
]
