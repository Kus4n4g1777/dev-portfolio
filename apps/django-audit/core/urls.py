from django.urls import path
from audit.views import health_check, get_logs

urlpatterns = [
    path('health/', health_check),
    path('api/logs/', get_logs),
]
