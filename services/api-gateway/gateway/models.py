from django.db import models
import uuid


class BlacklistedToken(models.Model):
    id = models.BigAutoField(primary_key=True)
    token = models.TextField(unique=True)
    blacklisted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    user_id = models.UUIDField(null=True, blank=True)
    
    class Meta:
        db_table = 'blacklisted_tokens'
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['user_id']),
        ]
    
    def __str__(self):
        return f"Blacklisted token for user {self.user_id}"


class RateLimitLog(models.Model):
    id = models.BigAutoField(primary_key=True)
    identifier = models.CharField(max_length=255)  # user_id or IP
    endpoint = models.CharField(max_length=100)
    action = models.CharField(max_length=20)  # 'allowed' or 'blocked'
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'rate_limit_logs'
        indexes = [
            models.Index(fields=['identifier']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.action} - {self.identifier} at {self.timestamp}"
