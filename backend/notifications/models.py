from django.db import models


class Notification(models.Model):
    recipient = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="notifications", null=True, blank=True
    )
    message = models.TextField()
    category = models.CharField(max_length=50, default="general")
    is_read = models.BooleanField(default=False, db_index=True)
    related_object_id = models.PositiveBigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.category}] {self.message[:50]}"
