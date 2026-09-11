from django.db import models

class User(models.Model):
    STUDENT = 'student'
    FACULTY = 'faculty'
    STAFF = 'staff'
    USER_TYPE_CHOICES = [
        (STUDENT, 'Student'),
        (FACULTY, 'Faculty'),
        (STAFF, 'Staff'),
    ]

    user_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default=STUDENT)
    department = models.CharField(max_length=100)