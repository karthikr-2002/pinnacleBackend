"""
URL configuration for pinnacleBackend project.
"""
from django.contrib import admin
from django.urls import path, include
from users import views as user_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('users.urls')),
    path('login/', user_views.login_view, name='login'),
    path('logout/', user_views.logout_view, name='logout'),
    path('register/', user_views.register_view, name='register'),
    path('', include('dashboard.urls')),
]
