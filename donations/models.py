from django.db import models
from django.contrib.auth.models import User
from projects.models import Project

class Donation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name="donations")
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.project.title}"



    
