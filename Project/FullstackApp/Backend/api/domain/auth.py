from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class UserManager(BaseUserManager):
    """
    Manager custom pentru User.
    BaseUserManager ne da utilitare de baza (make_password etc).
    Suprascriem create_user si create_superuser.
    """
    def create_user(self, email, password, role='student', **extra):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, role=role, **extra)
        user.set_password(password)   # hash-uieste parola cu bcrypt intern
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra):
        extra.setdefault('role', 'teacher')
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    """
    User model custom care inlocuieste User-ul built-in din Django.

    AbstractBaseUser   → ne da: password (hashed), last_login, is_active
    PermissionsMixin   → ne da: is_superuser, groups, user_permissions (necesar pt admin)

    Adaugam noi: email, first_name, last_name, role, is_staff.
    """
    ROLE_CHOICES = [('student', 'Student'), ('teacher', 'Teacher')]

    email      = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name  = models.CharField(max_length=100)
    role       = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    is_active  = models.BooleanField(default=True)
    is_staff   = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD  = 'email'      # folosim email in loc de username la login
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.role})"
