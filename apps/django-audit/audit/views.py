from django.http import JsonResponse
from django.db.models import Q
from .models import AuditLog

def health_check(request):
    return JsonResponse({"status": "healthy"})

def get_logs(request):
    limit    = int(request.GET.get('limit', 20))
    offset   = int(request.GET.get('offset', 0))
    runtime  = request.GET.get('runtime', '').strip()
    cache    = request.GET.get('cache', '').strip()    # 'hit' | 'miss' | ''

    qs = AuditLog.objects.order_by('-timestamp')

    if runtime:
        qs = qs.filter(payload__llm__runtime=runtime)

    if cache == 'hit':
        qs = qs.filter(payload__cache__hit=True)
    elif cache == 'miss':
        qs = qs.filter(payload__cache__hit=False)

    total = qs.count()
    logs  = list(qs.values('id', 'event_type', 'payload', 'timestamp')[offset:offset + limit])

    return JsonResponse({'total': total, 'logs': logs}, safe=False)
