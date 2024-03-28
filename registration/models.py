from django.db import models
from django.contrib.auth.models import User

class facts(models.Model):
    id = models.AutoField(primary_key=True)
    fact = models.CharField(max_length=255)

    def __str__(self):
        return self.fact

    class Meta:
        verbose_name_plural = "Facts"

class user_type(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=255)

    def __str__(self):
        return self.type