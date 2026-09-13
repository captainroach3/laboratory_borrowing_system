from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    STUDENT = 'student'
    FACULTY = 'faculty'
    STAFF = 'staff'
    USER_TYPE_CHOICES = [
        (STUDENT, 'Student'),
        (FACULTY, 'Faculty'),
        (STAFF, 'Staff'),
    ]

    user_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default=STUDENT)
    department = models.CharField(max_length=100)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'department']

    objects = UserManager()