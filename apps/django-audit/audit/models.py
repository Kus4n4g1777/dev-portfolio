from django.db import models

class AuditLog(models.Model):
    event_type = models.CharField(max_length=255)
    payload = models.JSONField()
    timestamp = models.DateTimeField(auto_now_add=True)
