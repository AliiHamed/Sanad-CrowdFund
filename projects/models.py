from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Project(models.Model):

    STATUS_CHOICES = [
        ("Draft", "Draft"),
        ("Active", "Active"),
        ("Completed", "Completed"),
        ("Cancelled", "Cancelled"),
    ]

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="projects",
        null=True,
        blank=True
    )

    title = models.CharField(max_length=200)

    description = models.TextField(blank=True, null=True)

    story = models.TextField(blank=True, null=True)

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projects"
    )

    target_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    current_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00
    )

    start_date = models.DateField(null=True, blank=True)

    end_date = models.DateField(null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Active"
    )

    tags = models.ManyToManyField(
        Tag,
        related_name="projects",
        blank=True
    )

    image = models.ImageField(
        upload_to="project_images/",
        blank=True,
        null=True
    )

    is_featured = models.BooleanField(default=False)

    def clean(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError(
                "End date must be after start date."
            )

    def __str__(self):
        return self.title


class ProjectImage(models.Model):

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="images"
    )

    image = models.ImageField(upload_to="project_images/")

    def __str__(self):
        return f"{self.project.title} Image"
    
