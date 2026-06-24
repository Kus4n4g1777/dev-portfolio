from django.http import JsonResponse
from .models import AuditLog

def health_check(request):
    return JsonResponse({"status": "healthy"})

def get_logs(request):
    logs = list(AuditLog.objects.values('id', 'event_type', 'payload', 'timestamp').order_by('-timestamp')[:50])
    return JsonResponse(logs, safe=False)
