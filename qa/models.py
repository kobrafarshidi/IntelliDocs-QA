from django.db import models


class QuestionAnswer(models.Model):
    question = models.TextField()
    answer = models.TextField(blank=True)
    sources = models.JSONField(default=list, blank=True)
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Q&A history"
        verbose_name_plural = "Q&A history"

    def __str__(self) -> str:
        return (self.question or "")[:80]
