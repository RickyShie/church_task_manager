from django.db import models

class Task(models.Model):
    task_name = models.CharField(max_length=200, null=False, unique=True)

class Department(models.Model):
    department_name = models.CharField(max_length=200, null=False, unique=True)

class Role(models.Model):
    role_name = models.CharField(max_length=200, null=False, unique=True)