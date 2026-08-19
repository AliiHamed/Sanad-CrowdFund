from django.db import models

class ChatLog(models.Model):
    user_message = models.TextField(verbose_name="سؤال المستخدم")
    bot_response = models.TextField(verbose_name="رد الذكاء الاصطناعي")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="وقت السؤال")

    def __str__(self):
        return f"Log: {self.user_message[:50]}..."
