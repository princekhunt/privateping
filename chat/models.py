from django.db import models
from django.utils import timezone


class UserProfile(models.Model):

    id = models.AutoField(primary_key=True, unique=True, editable=False, blank=True)
    name = models.CharField(max_length=25)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=20, unique=True)
    online = models.IntegerField(default=0)
    online_for = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.username}"


class Friends(models.Model):

    id = models.AutoField(primary_key=True, unique=True, editable=False, blank=True)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    friend = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="friend")

    def __str__(self):
        return f"{self.user} - {self.friend}"


#Store E2EE keys
class Keys(models.Model):
    id = models.AutoField(primary_key=True, unique=True, editable=False, blank=True)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    public_key = models.TextField()

    def __str__(self):
        return f"{self.user}"