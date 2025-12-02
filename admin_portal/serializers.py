from rest_framework import serializers
from .models import AdminUser, Department, Degree, Student, AlumniProfile, Poll, PollOption, Vote, Newsletter, NewsletterImage, SuccessStory, SuccessStoryImage, StudentVote
from django.utils import timezone
import datetime



class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminUser
        fields = ['id', 'email', 'last_login', 'is_active', 'is_staff', 'is_superuser']

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['department_id', 'department_name', 'email']

class DegreeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Degree
        fields = ['id', 'degree_name', 'duration_years']

from rest_framework import serializers
from .models import AdminUser, Department, Degree, Student, AlumniProfile, Poll, PollOption, Vote, Newsletter, NewsletterImage, SuccessStory, SuccessStoryImage, StudentVote
from django.utils import timezone
import datetime

class StudentSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = ['regno', 'name', 'email', 'phone', 'end_year', 'role', 'company_name', 'location', 'is_active']

    def get_role(self, obj):
        try:
            alumni = AlumniProfile.objects.get(regno=obj.regno)
            experience = alumni.experience_details
            if isinstance(experience, list) and len(experience) > 0:
                for exp in experience:
                    if exp.get('end_year') in ['Currently', 'Present']:
                        return exp.get('role', '') or ''
                return ''
            return ''
        except AlumniProfile.DoesNotExist:
            return ''
        except (TypeError, KeyError):
            return ''

    def get_company_name(self, obj):
        try:
            alumni = AlumniProfile.objects.get(regno=obj.regno)
            experience = alumni.experience_details
            if isinstance(experience, list) and len(experience) > 0:
                for exp in experience:
                    if exp.get('end_year') in ['Currently', 'Present']:
                        return exp.get('company_name', '') or ''
                return ''
            return ''
        except AlumniProfile.DoesNotExist:
            return ''
        except (TypeError, KeyError):
            return ''

    def get_location(self, obj):
        try:
            alumni = AlumniProfile.objects.get(regno=obj.regno)
            experience = alumni.experience_details
            if isinstance(experience, list) and len(experience) > 0:
                for exp in experience:
                    if exp.get('end_year') in ['Currently', 'Present']:
                        return exp.get('location', '') or ''
                return ''
            return ''
        except AlumniProfile.DoesNotExist:
            return ''
        except (TypeError, KeyError):
            return ''

            
    def get_is_active(self, obj):
        try:
            AlumniProfile.objects.get(regno=obj.regno)
            return True
        except AlumniProfile.DoesNotExist:
            return False



from rest_framework import serializers
from .models import Poll, PollOption, Vote, StudentVote, AdminUser


class PollOptionSerializer(serializers.ModelSerializer):
    vote_count = serializers.SerializerMethodField()

    class Meta:
        model = PollOption
        fields = ['id', 'text', 'vote_count']

    def get_vote_count(self, obj):
        return obj.votes.count() + obj.student_votes.filter(source='admin').count()

class PollSerializer(serializers.ModelSerializer):
    options = PollOptionSerializer(many=True, read_only=True)
    is_expired = serializers.SerializerMethodField()
    total_votes = serializers.SerializerMethodField()

    class Meta:
        model = Poll
        fields = ['id', 'question', 'created_at', 'deadline', 'is_active', 'is_expired', 'options', 'total_votes']

    def get_is_expired(self, obj):
        return obj.is_expired

    def get_total_votes(self, obj):
        total = 0
        for option in obj.options.all():
            total += option.votes.count() + option.student_votes.filter(source='admin').count()
        return total

class PollCreateSerializer(serializers.ModelSerializer):
    options = serializers.ListField(child=serializers.CharField(max_length=100), write_only=True)
    email = serializers.EmailField(write_only=True)  # Added to accept email from request

    class Meta:
        model = Poll
        fields = ['question', 'deadline', 'options', 'email']

    def validate_options(self, value):
        if len(value) < 2:
            raise serializers.ValidationError("At least two options are required.")
        if len(value) > 10:
            raise serializers.ValidationError("Maximum 10 options allowed.")
        return value

    def validate_email(self, value):
        try:
            user = AdminUser.objects.get(email=value)
            if not user.last_login or (timezone.now() - user.last_login).total_seconds() > 3600:
                raise serializers.ValidationError("User session expired or invalid.")
            return value
        except AdminUser.DoesNotExist:
            raise serializers.ValidationError("Invalid user email.")

    def create(self, validated_data):
        options = validated_data.pop('options')
        validated_data.pop('email', None)
        created_by = self.context['created_by']
        poll = Poll.objects.create(created_by=created_by, **validated_data)
        for option_text in options:
            PollOption.objects.create(poll=poll, text=option_text)
        return poll

    def update(self, instance, validated_data):
        options = validated_data.pop('options', None)
        validated_data.pop('email', None)  # Email not needed for update
        instance.question = validated_data.get('question', instance.question)
        instance.deadline = validated_data.get('deadline', instance.deadline)
        instance.save()
        if options:
            instance.options.all().delete()
            for option_text in options:
                PollOption.objects.create(poll=instance, text=option_text)
        return instance


class VoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vote
        fields = ['poll_option']

    def validate(self, data):
        poll = data['poll_option'].poll
        if poll.is_expired:
            raise serializers.ValidationError("This poll has expired.")
        user = self.context.get('user')
        if not isinstance(user, AdminUser):
            raise serializers.ValidationError("Invalid user")
        if Vote.objects.filter(poll_option__poll=poll, user=user).exists():
            raise serializers.ValidationError("You have already voted in this poll.")
        return data




from rest_framework import serializers
from .models import Newsletter, NewsletterImage, AdminUser

class NewsletterImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = NewsletterImage
        fields = ['id', 'image']
        read_only_fields = ['newsletter']

    def get_image(self, obj):
        if obj.image:
            # Return the full URL for the image
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            # Fallback for when request is not available
            return f"http://localhost:8000{obj.image.url}"
        return None

class NewsletterSerializer(serializers.ModelSerializer):
    images = NewsletterImageSerializer(many=True, read_only=True, source='images.all')
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(), write_only=True, required=False
    )

    class Meta:
        model = Newsletter
        fields = ['id', 'title', 'subtitle', 'description', 'url', 'status', 'created_at', 'updated_at', 'images', 'uploaded_images']
        read_only_fields = ['created_at', 'updated_at']

    def create(self, validated_data):
        uploaded_images = validated_data.pop('uploaded_images', [])
        # created_by is passed from the view, not from request.user
        newsletter = Newsletter.objects.create(**validated_data)
        for image in uploaded_images:
            try:
                NewsletterImage.objects.create(
                    newsletter=newsletter,
                    image=image
                )
            except Exception as e:
                newsletter.delete()
                raise serializers.ValidationError(f"Failed to save image: {str(e)}")
        return newsletter

    def update(self, instance, validated_data):
        uploaded_images = validated_data.pop('uploaded_images', [])
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        for image in uploaded_images:
            try:
                NewsletterImage.objects.create(
                    newsletter=instance,
                    image=image
                )
            except Exception as e:
                raise serializers.ValidationError(f"Failed to save image: {str(e)}")
        return instance
        
from rest_framework import serializers
from .models import SuccessStory, AdminUser


class SuccessStoryImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = SuccessStoryImage
        fields = ['id', 'image', 'success_story']
        read_only_fields = ['success_story']

    def get_image(self, obj):
        if obj.image:
            # Return the full URL for the image
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            # Fallback for when request is not available
            return f"http://localhost:8000{obj.image.url}"
        return None

class SuccessStorySerializer(serializers.ModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(queryset=AdminUser.objects.all(), required=False)
    expires_at = serializers.DateTimeField(required=False)
    
    images = SuccessStoryImageSerializer(many=True, read_only=True)
    class Meta:
        model = SuccessStory
        fields = ['id', 'title', 'description', 'url', 'created_at', 'created_by', 'expires_at', 'images']
        read_only_fields = ['created_at']

    def create(self, validated_data):
        # Ensure created_by is set from context if not in validated_data
        created_by = validated_data.pop('created_by', self.context.get('created_by'))
        # Ensure expires_at is set if not provided
        expires_at = validated_data.pop('expires_at', timezone.now() + datetime.timedelta(days=365))
        return SuccessStory.objects.create(created_by=created_by, expires_at=expires_at, **validated_data)

from rest_framework import serializers
from .models import Department, Degree, Student, AlumniFeedback
import logging

logger = logging.getLogger(__name__)

class AlumniFeedbackSerializer(serializers.ModelSerializer):
    date = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()
    degree_name = serializers.SerializerMethodField()

    class Meta:
        model = AlumniFeedback
        fields = [
            'id', 'user_name', 'user_email', 'category', 'rating', 'comment',
            'date', 'is_read', 'is_flagged', 'for_admin', 'for_dept',
            'department_id', 'degree_id', 'department_name', 'degree_name'
        ]
        read_only_fields = ['id', 'created_at', 'for_admin', 'for_dept', 'department_id', 'degree_id', 'department_name', 'degree_name']

    def get_date(self, obj):
        return obj.created_at.strftime('%Y-%m-%d')

    def get_department_name(self, obj):
        try:
            student = Student.objects.filter(
                email=obj.user_email,
                department_id=obj.department_id,
                degree_id=obj.degree_id
            ).first()
            return student.department_name if student else 'Unknown Department'
        except Exception as e:
            logger.error(f"Error fetching department_name for feedback {obj.id}: {str(e)}")
            return 'Unknown Department'

    def get_degree_name(self, obj):
        try:
            student = Student.objects.filter(
                email=obj.user_email,
                department_id=obj.department_id,
                degree_id=obj.degree_id
            ).first()
            return student.degree_name if student else 'Unknown Degree'
        except Exception as e:
            logger.error(f"Error fetching degree_name for feedback {obj.id}: {str(e)}")
            return 'Unknown Degree'