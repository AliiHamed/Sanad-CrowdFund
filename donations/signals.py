from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum

from .models import Donation


@receiver(post_save, sender=Donation)
def update_project_amount(sender, instance, **kwargs):

    project = instance.project

    total = Donation.objects.filter(
        project=project
    ).aggregate(
        Sum('amount')
    )['amount__sum']

    project.current_amount = total or 0
    project.save()


    