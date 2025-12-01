from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
import datetime

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
import datetime

class AdminUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class AdminUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=191, unique=True)
    password = models.CharField(max_length=256)
    last_login = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = AdminUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='adminuser_groups',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='adminuser_permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    def __str__(self):
        return self.email

    @property
    def is_authenticated(self):
        return True

class CurrentlyLoggedInUser(models.Model):
    email = models.EmailField(max_length=191, unique=True)
    login_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email

class AdminOTP(models.Model):
    email = models.EmailField(max_length=191)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + datetime.timedelta(minutes=5)

class Department(models.Model):
    department_id = models.CharField(max_length=50, unique=True, primary_key=True)
    department_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.department_name} ({self.department_id})"

class Degree(models.Model):
    department = models.ForeignKey(Department, related_name='degrees', on_delete=models.CASCADE)
    degree_name = models.CharField(max_length=100, db_column='degree_name')  # Map to table column
    duration_years = models.IntegerField()

    def __str__(self):
        return f"{self.degree_name} ({self.department.department_name})"

    class Meta:
        db_table = 'department_degrees'  # Explicitly set table name


class Student(models.Model):
    regno = models.CharField(max_length=50, unique=True, db_column='regno')
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=254)
    phone = models.CharField(max_length=15, db_column='phone')
    degree = models.ForeignKey(Degree, related_name='students', on_delete=models.CASCADE)
    department_id = models.CharField(max_length=50)
    department_name = models.CharField(max_length=100)
    degree_name = models.CharField(max_length=100)
    start_year = models.IntegerField()
    end_year = models.IntegerField()
    blood_group = models.CharField(max_length=10, blank=True)

    def __str__(self):
        return f"{self.name} ({self.regno})"

    class Meta:
        db_table = 'department_students'

class AlumniProfile(models.Model):
    regno = models.CharField(max_length=50, unique=True, primary_key=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=254)
    phone = models.CharField(max_length=15)
    blood_group = models.CharField(max_length=10, blank=True)
    dob = models.DateField(null=True, blank=True)
    about = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True)
    education_details = models.JSONField(blank=True, null=True)
    experience_details = models.JSONField(blank=True, null=True)
    profile_picture_url = models.URLField(max_length=255, blank=True)
    avatar_config = models.JSONField(blank=True, null=True)
    linkedin_url = models.URLField(max_length=255, blank=True)
    github_url = models.URLField(max_length=255, blank=True)
    portfolio_url = models.URLField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.name} ({self.regno})"

    class Meta:
        db_table = 'alumni_profiles'


class JobPost(models.Model):
    user_email = models.EmailField(max_length=254)
    company_name = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    company_website = models.URLField(max_length=255)
    job_id = models.CharField(max_length=50)
    job_title = models.CharField(max_length=100)
    job_type = models.CharField(max_length=50)
    application_deadline = models.DateField()
    job_description = models.TextField()
    experience_min = models.IntegerField()
    experience_max = models.IntegerField()
    salary_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_negotiable = models.BooleanField(default=False)
    is_paid_internship = models.BooleanField(default=False)
    stipend_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stipend_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stipend_based_on_performance = models.BooleanField(default=False)
    duration_value = models.IntegerField(null=True, blank=True)
    duration_type = models.CharField(max_length=10, blank=True)
    skills = models.JSONField(blank=True, null=True)
    qualifications = models.TextField(blank=True)
    application_email = models.EmailField(max_length=254, blank=True)
    application_url = models.URLField(max_length=255, blank=True)
    application_image = models.URLField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    job_image = models.URLField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.job_title} at {self.company_name}"

    class Meta:
        db_table = 'job_posts'


from django.db import models
from django.utils import timezone

class Poll(models.Model):
    question = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    deadline = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey('AdminUser', on_delete=models.CASCADE)

    class Meta:
        ordering = ['-created_at']
        db_table = 'admin_portal_poll'

    def __str__(self):
        return self.question

    @property
    def is_expired(self):
        return timezone.now() > self.deadline

class PollOption(models.Model):
    poll = models.ForeignKey(Poll, related_name='options', on_delete=models.CASCADE)
    text = models.CharField(max_length=100)

    class Meta:
        db_table = 'admin_portal_polloption'

    def __str__(self):
        return self.text
        
class Vote(models.Model):
    poll_option = models.ForeignKey(PollOption, related_name='votes', on_delete=models.CASCADE)
    user = models.ForeignKey('AdminUser', on_delete=models.CASCADE)
    voted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('poll_option', 'user')
        db_table = 'admin_portal_vote'

    def __str__(self):
        return f"Vote for {self.poll_option.text} by {self.user.email}"

class StudentVote(models.Model):
    question = models.TextField()
    poll_option = models.ForeignKey(PollOption, related_name='student_votes', on_delete=models.CASCADE)
    user = models.ForeignKey('AdminUser', on_delete=models.CASCADE)
    source = models.CharField(max_length=10)
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    voted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'student_vote'

    def __str__(self):
        return f"Student vote for {self.poll_option.text} by {self.user.email}"



class NewsletterImage(models.Model):
    image = models.ImageField(upload_to='newsletters/')
    newsletter = models.ForeignKey('Newsletter', related_name='images', on_delete=models.CASCADE)

    def __str__(self):
        return f"Image for {self.newsletter.title}"

class Newsletter(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
    )

    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField()
    url = models.URLField(max_length=500, blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        AdminUser,
        on_delete=models.CASCADE,
        related_name='newsletters'
    )

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']


class SuccessStory(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    url = models.URLField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(AdminUser, on_delete=models.CASCADE)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + datetime.timedelta(days=365)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']

class SuccessStoryImage(models.Model):
    image = models.ImageField(upload_to='success_stories/')
    success_story = models.ForeignKey(SuccessStory, related_name='images', on_delete=models.CASCADE)

    def __str__(self):
        return f"Image for {self.success_story.title}"

# ... (Other models remain unchanged: AdminUser, AdminUserManager, CurrentlyLoggedInUser, AdminOTP, Department, Degree, Student, AlumniProfile, JobPost, Poll, PollOption, Vote, StudentVote, Newsletter, NewsletterImage, SuccessStory, SuccessStoryImage)

class AlumniFeedback(models.Model):
    user_email = models.CharField(max_length=255, db_column='user_email')
    category = models.CharField(max_length=100)
    rating = models.IntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(db_column='created_at')
    is_read = models.BooleanField(default=False, db_column='is_read')
    is_flagged = models.BooleanField(default=False, db_column='is_flagged')
    for_admin = models.BooleanField(default=False, db_column='for_admin')
    for_dept = models.BooleanField(default=False, db_column='for_dept')
    department_id = models.CharField(max_length=50, db_column='department_id')
    degree_id = models.BigIntegerField(db_column='degree_id')
    user_name = models.CharField(max_length=100, db_column='user_name')

    class Meta:
        db_table = 'alumni_feedback'
        ordering = ['-created_at']

    def __str__(self):
        return f"Feedback from {self.user_name} ({self.category})"

    @property
    def date(self):
        return self.created_at.strftime('%Y-%m-%d')

