from django.db import models
from django.contrib.auth.models import User
from projects.models import Project
from django.core.validators import MinValueValidator, MaxValueValidator

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="interaction_comments")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="interaction_comments_project")
    comment = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.comment[:20]


class Reply(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="interaction_replies")
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name="interaction_comment_replies")
    reply = models.TextField()

    def __str__(self):
        return self.reply[:20]


class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="interaction_ratings")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="interaction_project_ratings")
    rate = models.IntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5)
        ]
    )

    class Meta:
        unique_together = [['user', 'project']]

    def __str__(self):
        return f"{self.project.title} - {self.rate}"


class Report(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="interaction_reports")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="interaction_reports_project")
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True, related_name="interaction_reports_comment")
    reason = models.TextField()

    def __str__(self):
        return self.user.username