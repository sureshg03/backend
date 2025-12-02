from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password, check_password
from django.views.decorators.http import require_http_methods
from django.contrib.auth import login
import json
import logging
from .models import AdminUser, AdminOTP, Department, Degree, Student,AlumniProfile, Poll, CurrentlyLoggedInUser, Newsletter, NewsletterImage
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from rest_framework import status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from .serializers import DepartmentSerializer, DegreeSerializer, StudentSerializer, PollSerializer, PollCreateSerializer, VoteSerializer, NewsletterSerializer
from rest_framework.views import APIView
from django.utils.decorators import method_decorator



logger = logging.getLogger(__name__)

@require_http_methods(["GET"])
def check_admin_exists(request):
    exists = AdminUser.objects.exists()
    return JsonResponse({"exists": exists})

@csrf_exempt
@require_http_methods(["POST"])
def create_admin(request):
    try:
        data = json.loads(request.body)
        email = data.get("email")
        password = data.get("password")
        if AdminUser.objects.filter(email=email).exists():
            return JsonResponse({"error": "Admin already exists"}, status=400)

        hashed_password = make_password(password)
        AdminUser.objects.create(email=email, password=hashed_password)
        return JsonResponse({"status": "success"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def login_view(request):
    try:
        logger.info(f"Request body: {request.body}")
        data = json.loads(request.body)
        email = data.get("email")
        password = data.get("password")
        logger.info(f"Parsed email: {email}, password: {password}")

        if not email or not password:
            return JsonResponse({"status": "fail", "message": "Email and password are required"}, status=400)

        try:
            admin = AdminUser.objects.get(email=email)
        except AdminUser.DoesNotExist:
            return JsonResponse({"status": "fail", "message": "User not found"}, status=404)

        if check_password(password, admin.password):
            admin.last_login = timezone.now()
            admin.save(update_fields=['last_login'])
            login(request, admin, backend='admin_portal.authentication.AdminUserBackend')
            
            CurrentlyLoggedInUser.objects.filter(email=email).delete()
            CurrentlyLoggedInUser.objects.create(email=email)
            
            logger.info(f"User logged in: {admin.email}, last_login: {admin.last_login}")
            return JsonResponse({"status": "success", "message": "Login successful", "email": admin.email})
        else:
            return JsonResponse({"status": "fail", "message": "Incorrect password"}, status=401)
    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body")
        return JsonResponse({"status": "fail", "message": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        return JsonResponse({"status": "fail", "message": str(e)}, status=400)



@csrf_exempt
@require_http_methods(["POST"])
def logout_view(request):
    try:
        data = json.loads(request.body)
        email = data.get("email")
        
        if not email:
            return JsonResponse({"status": "fail", "message": "Email is required"}, status=400)
        
        CurrentlyLoggedInUser.objects.filter(email=email).delete()
        logger.info(f"User logged out: {email}")
        return JsonResponse({"status": "success", "message": "Logout successful"})
    except Exception as e:
        logger.error(f"Logout failed: {str(e)}")
        return JsonResponse({"status": "fail", "message": str(e)}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def send_otp(request):
    try:
        data = json.loads(request.body)
        email = data.get("email")

        if not AdminUser.objects.filter(email=email).exists():
            return JsonResponse({"status": "fail", "message": "Email not registered."}, status=404)

        otp = get_random_string(length=6, allowed_chars='0123456789')
        AdminOTP.objects.create(email=email, otp=otp)

        send_mail(
            subject="Your OTP for Password Reset",
            message=f"Use this OTP to reset your password: {otp}. It expires in 5 minutes.",
            from_email="periyaruniversity08@gmail.com",
            recipient_list=[email],
        )

        return JsonResponse({"status": "success", "message": "OTP sent to email."})
    except Exception as e:
        logger.error(f"send_otp failed: {e}")
        return JsonResponse({"status": "fail", "message": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def verify_otp(request):
    try:
        data = json.loads(request.body)
        email = data.get("email")
        otp_input = data.get("otp")

        if not email or not otp_input:
            return JsonResponse({"status": "fail", "message": "Email and OTP are required."}, status=400)

        otp_obj = AdminOTP.objects.filter(email=email).latest('created_at')

        if otp_obj.is_expired():
            return JsonResponse({"status": "fail", "message": "OTP expired."}, status=400)
        if otp_obj.otp != otp_input:
            return JsonResponse({"status": "fail", "message": "Invalid OTP."}, status=400)

        return JsonResponse({"status": "success", "message": "OTP verified."})
    except AdminOTP.DoesNotExist:
        return JsonResponse({"status": "fail", "message": "No OTP found for this email."}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({"status": "fail", "message": "Invalid JSON"}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def reset_password(request):
    try:
        data = json.loads(request.body)
        email = data.get("email")
        new_password = data.get("password")

        if not email or not new_password:
            return JsonResponse({"status": "fail", "message": "Email and password are required."}, status=400)

        user = AdminUser.objects.get(email=email)
        user.password = make_password(new_password)
        user.save()

        return JsonResponse({"status": "success", "message": "Password updated successfully."})
    except AdminUser.DoesNotExist:
        return JsonResponse({"status": "fail", "message": "User not found."}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({"status": "fail", "message": "Invalid JSON"}, status=400)

from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import logging
from .models import AdminUser, CurrentlyLoggedInUser

logger = logging.getLogger(__name__)

@api_view(['GET'])
@csrf_exempt
def get_current_user(request):
    try:
        current_user = CurrentlyLoggedInUser.objects.first()
        if not current_user:
            return Response({"message": "No user is currently logged in"}, status=status.HTTP_404_NOT_FOUND)
        
        admin_user = AdminUser.objects.filter(email=current_user.email).first()
        if not admin_user:
            return Response({"message": "Admin user not found"}, status=status.HTTP_404_NOT_FOUND)
        
        data = {
            "email": admin_user.email,
            "last_login": admin_user.last_login,
            "is_active": admin_user.is_active,
            "is_staff": admin_user.is_staff,
            "is_superuser": admin_user.is_superuser,
            "login_time": current_user.login_time,
        }
        return Response(data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Failed to fetch current user: {str(e)}")
        return Response({"message": f"Failed to fetch current user: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@csrf_exempt
def debug_current_user(request):
    try:
        current_user = CurrentlyLoggedInUser.objects.first()
        if current_user:
            return Response({
                "email": current_user.email,
                "message": "User is logged in"
            })
        else:
            return Response({
                "message": "No user is currently logged in"
            }, status=404)
    except Exception as e:
        logger.error(f"Failed to fetch current user: {str(e)}")
        return Response({"message": f"Failed to fetch current user: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password, check_password
from django.views.decorators.http import require_http_methods
from django.contrib.auth import login
import json
import logging
from .models import AdminUser, AdminOTP, Department, Degree, Student, AlumniProfile, Poll, CurrentlyLoggedInUser, Newsletter, JobPost
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from .serializers import DepartmentSerializer, DegreeSerializer, StudentSerializer, PollSerializer, PollCreateSerializer, VoteSerializer, NewsletterSerializer
from rest_framework.views import APIView
from django.utils import timezone
from .serializers import SuccessStorySerializer, SuccessStoryImageSerializer
import datetime

logger = logging.getLogger(__name__)

@api_view(['GET'])
@csrf_exempt
def get_dashboard_stats(request):
    try:
        current_user = CurrentlyLoggedInUser.objects.first()
        if not current_user:
            logger.error("No currently logged-in user found")
            return Response({"message": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        
        email = current_user.email
        user = AdminUser.objects.filter(email=email).order_by('-last_login').first()
        if not user or not user.last_login or (timezone.now() - user.last_login).total_seconds() > 3600:
            logger.error(f"Invalid or expired login for email: {email}")
            CurrentlyLoggedInUser.objects.filter(email=email).delete()
            return Response({"message": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        
        department_count = Department.objects.count()
        student_count = Student.objects.count()
        alumni_count = AlumniProfile.objects.count()
        job_count = JobPost.objects.count()
        logger.info(f"Fetched dashboard stats for user: {user.email}")
        return Response({
            "total_departments": department_count,
            "total_students": student_count,
            "total_alumni": alumni_count,
            "total_jobs": job_count
        }, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Failed to fetch dashboard stats: {str(e)}")
        return Response({"message": f"Failed to fetch dashboard stats: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password, check_password
from django.views.decorators.http import require_http_methods
from django.contrib.auth import login
import json
import logging
from .models import AdminUser, AdminOTP, Department, Degree, Student, AlumniProfile, Poll, CurrentlyLoggedInUser, Newsletter, JobPost
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from .serializers import DepartmentSerializer, DegreeSerializer, StudentSerializer, PollSerializer, PollCreateSerializer, VoteSerializer, NewsletterSerializer
from rest_framework.views import APIView
from django.utils import timezone
from .serializers import SuccessStorySerializer, SuccessStoryImageSerializer
import datetime
from django.db.models import Count

logger = logging.getLogger(__name__)

@api_view(['GET'])
@csrf_exempt
def get_department_student_counts(request):
    try:
        current_user = CurrentlyLoggedInUser.objects.first()
        if not current_user:
            logger.error("No currently logged-in user found")
            return Response({"message": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        
        email = current_user.email
        user = AdminUser.objects.filter(email=email).order_by('-last_login').first()
        if not user or not user.last_login or (timezone.now() - user.last_login).total_seconds() > 3600:
            logger.error(f"Invalid or expired login for email: {email}")
            CurrentlyLoggedInUser.objects.filter(email=email).delete()
            return Response({"message": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        
        student_counts = (
            Student.objects
            .values('department_name')
            .annotate(student_count=Count('id'))
            .order_by('department_name')
        )
        student_count_dict = {item['department_name']: item['student_count'] for item in student_counts}

        all_departments = Department.objects.values('department_name').order_by('department_name')

        data = [
            {
                'department_name': dept['department_name'],
                'student_count': student_count_dict.get(dept['department_name'], 0)
            }
            for dept in all_departments
        ]

        logger.info(f"Fetched department-wise student counts for user: {user.email}")
        return Response(data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Failed to fetch department student counts: {str(e)}")
        return Response({"message": f"Failed to fetch department student counts: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)        
        


from django.db.models import Count

@api_view(['GET'])
@csrf_exempt
def get_active_student_counts(request):
    try:
        current_user = CurrentlyLoggedInUser.objects.first()
        if not current_user:
            logger.error("No currently logged-in user found")
            return Response({"message": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        
        email = current_user.email
        user = AdminUser.objects.filter(email=email).order_by('-last_login').first()
        if not user or not user.last_login or (timezone.now() - user.last_login).total_seconds() > 3600:
            logger.error(f"Invalid or expired login for email: {email}")
            CurrentlyLoggedInUser.objects.filter(email=email).delete()
            return Response({"message": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        # Join alumni_profiles with department_students on regno and group by department_name
        active_counts = (
            Student.objects
            .filter(regno__in=AlumniProfile.objects.values('regno'))
            .values('department_name')
            .annotate(active_student_count=Count('id'))
            .order_by('department_name')
        )
        # Convert to dict for easier lookup
        active_count_dict = {item['department_name']: item['active_student_count'] for item in active_counts}

        # Get all department names from admin_portal_department
        all_departments = Department.objects.values('department_name').order_by('department_name')

        # Merge to include departments with zero active students
        data = [
            {
                'department_name': dept['department_name'],
                'active_student_count': active_count_dict.get(dept['department_name'], 0)
            }
            for dept in all_departments
        ]

        logger.info(f"Fetched active student counts: {len(data)} departments")
        return Response(data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Failed to fetch active student counts: {str(e)}")
        return Response({"message": f"Failed to fetch active student counts: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password, check_password
from django.views.decorators.http import require_http_methods
from django.contrib.auth import login
import json
import logging
from .models import AdminUser, AdminOTP, Department, Degree, Student, AlumniProfile, Poll, CurrentlyLoggedInUser, Newsletter, JobPost
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from .serializers import DepartmentSerializer, DegreeSerializer, StudentSerializer, PollSerializer, PollCreateSerializer, VoteSerializer, NewsletterSerializer
from rest_framework.views import APIView
from django.utils import timezone
from .serializers import SuccessStorySerializer, SuccessStoryImageSerializer
import datetime
from django.db.models import Count

logger = logging.getLogger(__name__)

@api_view(['GET'])
@csrf_exempt
def get_alumni_status_counts(request):
    try:
        current_user = CurrentlyLoggedInUser.objects.first()
        if not current_user:
            logger.error("No currently logged-in user found")
            return Response({"message": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        
        email = current_user.email
        user = AdminUser.objects.filter(email=email).order_by('-last_login').first()
        if not user or not user.last_login or (timezone.now() - user.last_login).total_seconds() > 3600:
            logger.error(f"Invalid or expired login for email: {email}")
            CurrentlyLoggedInUser.objects.filter(email=email).delete()
            return Response({"message": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        # Fetch all alumni profiles
        alumni = AlumniProfile.objects.all()
        employed_count = 0
        unemployed_count = 0

        for alum in alumni:
            experience = alum.experience_details
            if isinstance(experience, list) and len(experience) > 0:
                # Check if any experience entry has end_year as "Currently" or "Present"
                is_employed = any(
                    exp.get('end_year') in ['Currently', 'Present']
                    for exp in experience
                )
                if is_employed:
                    employed_count += 1
                else:
                    unemployed_count += 1
            else:
                unemployed_count += 1

        data = [
            {'status': 'Employed', 'count': employed_count},
            {'status': 'Unemployed', 'count': unemployed_count},
        ]
        logger.info(f"Fetched alumni status counts: Employed={employed_count}, Unemployed={unemployed_count}")
        return Response(data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Failed to fetch alumni status counts: {str(e)}")
        return Response({"message": f"Failed to fetch alumni status counts: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



from django.db.models import Count
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import logging

from django.db.models import Count
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

@api_view(['GET'])
def get_job_counts(request):
    try:
        current_user = CurrentlyLoggedInUser.objects.first()
        if not current_user:
            logger.error("No currently logged-in user found")
            return Response({"message": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        
        email = current_user.email
        user = AdminUser.objects.filter(email=email).order_by('-last_login').first()
        if not user or not user.last_login or (timezone.now() - user.last_login).total_seconds() > 3600:
            logger.error(f"Invalid or expired login for email: {email}")
            CurrentlyLoggedInUser.objects.filter(email=email).delete()
            return Response({"message": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        # Fetch total job posts
        total_jobs = JobPost.objects.count()
        # Fetch total unique companies
        total_companies = JobPost.objects.values('company_name').distinct().count()
        # Fetch job counts per company
        company_counts = JobPost.objects.values('company_name').annotate(job_count=Count('id')).order_by('-job_count')

        data = {
            'total_jobs': total_jobs,
            'total_companies': total_companies,
            'company_counts': list(company_counts),
        }
        logger.info(f"Fetched job counts: Total Jobs={total_jobs}, Total Companies={total_companies}, Companies={len(company_counts)}")
        return Response(data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Failed to fetch job counts: {str(e)}")
        return Response({"message": f"Failed to fetch job counts: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AddDepartmentView(APIView):
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        try:
            logger.info("add_department called")
            logger.info(f"Request data: {request.data}")
            
            serializer = DepartmentSerializer(data=request.data)
            if serializer.is_valid():
                department = serializer.save()
                logger.info(f"Department saved successfully: {department.department_id}")
                return Response({
                    "message": "Department added successfully!",
                    "department": {
                        "department_id": department.department_id,
                        "department_name": department.department_name,
                        "email": department.email
                    }
                }, status=status.HTTP_201_CREATED)
            
            logger.error(f"Serializer errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error adding department: {str(e)}")
            return Response({"message": f"Error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

add_department = AddDepartmentView.as_view()

@api_view(['PUT'])
@csrf_exempt
def update_department(request, department_id):
    try:
        current_user = CurrentlyLoggedInUser.objects.first()
        if not current_user:
            logger.error("No currently logged-in user found")
            return Response({"message": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        
        email = current_user.email
        user = AdminUser.objects.filter(email=email).order_by('-last_login').first()
        if not user or not user.last_login or (timezone.now() - user.last_login).total_seconds() > 3600:
            logger.error(f"Invalid or expired login for email: {email}")
            CurrentlyLoggedInUser.objects.filter(email=email).delete()
            return Response({"message": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        department = Department.objects.get(department_id=department_id)
        serializer = DepartmentSerializer(department, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"Department {department_id} updated successfully")
            return Response({"message": "Department updated successfully!"}, status=status.HTTP_200_OK)
        logger.error(f"Serializer errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Department.DoesNotExist:
        logger.error(f"Department {department_id} not found")
        return Response({"message": "Department not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['DELETE'])
@csrf_exempt
def delete_department(request, department_id):
    try:
        current_user = CurrentlyLoggedInUser.objects.first()
        if not current_user:
            logger.error("No currently logged-in user found")
            return Response({"message": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        
        email = current_user.email
        user = AdminUser.objects.filter(email=email).order_by('-last_login').first()
        if not user or not user.last_login or (timezone.now() - user.last_login).total_seconds() > 3600:
            logger.error(f"Invalid or expired login for email: {email}")
            CurrentlyLoggedInUser.objects.filter(email=email).delete()
            return Response({"message": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        department = Department.objects.get(department_id=department_id)
        department.delete()
        logger.info(f"Department {department_id} deleted successfully")
        return Response({"message": "Department deleted successfully!"}, status=status.HTTP_204_NO_CONTENT)
    except Department.DoesNotExist:
        logger.error(f"Department {department_id} not found")
        return Response({"message": "Department not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['DELETE'])
@csrf_exempt
def delete_all_departments(request):
    try:
        current_user = CurrentlyLoggedInUser.objects.first()
        if not current_user:
            logger.error("No currently logged-in user found")
            return Response({"message": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        
        email = current_user.email
        user = AdminUser.objects.filter(email=email).order_by('-last_login').first()
        if not user or not user.last_login or (timezone.now() - user.last_login).total_seconds() > 3600:
            logger.error(f"Invalid or expired login for email: {email}")
            CurrentlyLoggedInUser.objects.filter(email=email).delete()
            return Response({"message": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        Department.objects.all().delete()
        logger.info("All departments deleted successfully")
        return Response({"message": "All departments deleted successfully!"}, status=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        logger.error(f"Failed to delete all departments: {str(e)}")
        return Response({"message": f"Failed to delete all departments: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@csrf_exempt
def get_departments(request):
    try:
        current_user = CurrentlyLoggedInUser.objects.first()
        if not current_user:
            logger.error("No currently logged-in user found")
            return Response({"message": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        
        email = current_user.email
        user = AdminUser.objects.filter(email=email).order_by('-last_login').first()
        if not user or not user.last_login or (timezone.now() - user.last_login).total_seconds() > 3600:
            logger.error(f"Invalid or expired login for email: {email}")
            CurrentlyLoggedInUser.objects.filter(email=email).delete()
            return Response({"message": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        departments = Department.objects.all()
        logger.info(f"Fetched {departments.count()} departments")
        serializer = DepartmentSerializer(departments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Failed to fetch departments: {str(e)}")
        return Response({"message": f"Failed to fetch departments: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class DepartmentListView(APIView):
    def get(self, request):
        departments = Department.objects.all()
        serializer = DepartmentSerializer(departments, many=True)
        return Response(serializer.data)


class DegreeListView(APIView):
    def get(self, request, department_id):
        try:
            # Check if department exists
            Department.objects.get(department_id=department_id)
            # Use the foreign key relationship to filter degrees
            degrees = Degree.objects.filter(department__department_id=department_id)
            logger.info(f"Fetched {degrees.count()} degrees for department {department_id}")
            serializer = DegreeSerializer(degrees, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Department.DoesNotExist:
            logger.error(f"Department {department_id} not found")
            return Response({"message": "Department not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error fetching degrees for department {department_id}: {str(e)}")
            return Response({"message": f"Error fetching degrees: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class StudentListView(APIView):
    def get(self, request, degree_id):
        try:
            students = Student.objects.filter(degree_id=degree_id)
            logger.info(f"Fetched {students.count()} students for degree {degree_id}")
            serializer = StudentSerializer(students, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching students for degree {degree_id}: {str(e)}")
            return Response({"message": f"Error fetching students: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from .models import Poll, Vote, AdminUser
from .serializers import PollSerializer, PollCreateSerializer, VoteSerializer
import logging

logger = logging.getLogger(__name__)

@api_view(['GET', 'POST'])
@csrf_exempt
def poll_list_create(request):
    if request.method == 'GET':
        active_polls = Poll.objects.filter(is_active=True)
        past_polls = Poll.objects.filter(is_active=False)
        active_serializer = PollSerializer(active_polls, many=True)
        past_serializer = PollSerializer(past_polls, many=True)
        logger.info("Fetched all polls")
        return Response({
            'active_polls': active_serializer.data,
            'past_polls': past_serializer.data
        }, status=status.HTTP_200_OK)
    elif request.method == 'POST':
        email = request.data.get('email')
        
        if not email:
            logger.error("No email provided in request")
            return Response({"message": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        user = AdminUser.objects.filter(email=email).order_by('-last_login').first()
        if not user or not user.last_login or (timezone.now() - user.last_login).total_seconds() > 3600:
            logger.error(f"Invalid or expired login for email: {email}")
            return Response({"message": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        
        logger.info(f"Authenticated user: {user.email}, last_login: {user.last_login}")
        
        serializer = PollCreateSerializer(data=request.data, context={'created_by': user})
        if serializer.is_valid():
            poll = serializer.save()
            logger.info(f"Poll created successfully by user: {user.email}")
            return Response({"message": "Poll created successfully!", "data": PollSerializer(poll).data}, status=status.HTTP_201_CREATED)
        logger.error(f"Poll creation failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@csrf_exempt
def update_poll(request, poll_id):
    try:
        email = request.data.get('email')
        user = AdminUser.objects.filter(email=email).order_by('-last_login').first()
        if not user or not user.last_login or (timezone.now() - user.last_login).total_seconds() > 3600:
            logger.error(f"Invalid or expired login for email: {email}")
            return Response({"message": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        
        poll = Poll.objects.get(id=poll_id)
        serializer = PollCreateSerializer(poll, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"Poll {poll_id} updated successfully by user: {email}")
            return Response({"message": "Poll updated successfully!", "data": serializer.data}, status=status.HTTP_200_OK)
        logger.error(f"Poll update failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Poll.DoesNotExist:
        logger.error(f"Poll {poll_id} not found")
        return Response({"message": "Poll not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Poll update error: {str(e)}")
        return Response({"message": f"Failed to update poll: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@csrf_exempt
def get_user_votes(request):
    try:
        email = request.query_params.get('email')
        if not email:
            logger.error("No email provided in request")
            return Response({"message": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        user = AdminUser.objects.filter(email=email).order_by('-last_login').first()
        if not user:
            logger.error(f"No user found for email: {email}")
            return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        
        votes = Vote.objects.filter(user=user).values('poll_option__poll__id').distinct()
        vote_data = [{"poll_id": vote['poll_option__poll__id']} for vote in votes]
        logger.info(f"Fetched votes for user: {email}")
        return Response(vote_data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Failed to fetch user votes: {str(e)}")
        return Response({"message": f"Failed to fetch votes: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@csrf_exempt
def vote_poll(request, poll_id):
    try:
        email = request.data.get('email')
        user = AdminUser.objects.filter(email=email).order_by('-last_login').first()
        if not user or not user.last_login or (timezone.now() - user.last_login).total_seconds() > 3600:
            logger.error(f"Invalid or expired login for email: {email}")
            return Response({"message": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        
        poll = Poll.objects.get(id=poll_id)
        serializer = VoteSerializer(data=request.data, context={'user': user})
        if serializer.is_valid():
            serializer.validated_data['poll_option'].poll = poll
            serializer.save(user=user)
            logger.info(f"Vote recorded for poll {poll_id} by user: {user.email}")
            return Response({"message": "Vote recorded successfully!"}, status=status.HTTP_201_CREATED)
        logger.error(f"Vote failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Poll.DoesNotExist:
        logger.error(f"Poll {poll_id} not found")
        return Response({"message": "Poll not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Vote error: {str(e)}")
        return Response({"message": f"Failed to record vote: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@csrf_exempt
def move_to_past(request, poll_id):
    logger.info(f"Received request to move poll {poll_id} to past")
    try:
        email = request.data.get('email')
        user = AdminUser.objects.filter(email=email).order_by('-last_login').first()
        if not user or not user.last_login or (timezone.now() - user.last_login).total_seconds() > 3600:
            logger.error(f"Invalid or expired login for email: {email}")
            return Response({"message": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        
        poll = Poll.objects.get(id=poll_id)
        poll.is_active = False
        poll.save()
        logger.info(f"Poll {poll_id} moved to past polls by user: {user.email}")
        return Response({"message": "Poll moved to past polls!"}, status=status.HTTP_200_OK)
    except Poll.DoesNotExist:
        logger.error(f"Poll {poll_id} not found")
        return Response({"message": "Poll not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Move to past error: {str(e)}")
        return Response({"message": f"Failed to move poll: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
@csrf_exempt
def delete_poll(request, poll_id):
    try:
        email = request.data.get('email')
        user = AdminUser.objects.filter(email=email).order_by('-last_login').first()
        if not user or not user.last_login or (timezone.now() - user.last_login).total_seconds() > 3600:
            logger.error(f"Invalid or expired login for email: {email}")
            return Response({"message": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        
        poll = Poll.objects.get(id=poll_id)
        poll.delete()
        logger.info(f"Poll {poll_id} deleted successfully by user: {user.email}")
        return Response({"message": "Poll deleted successfully!"}, status=status.HTTP_204_NO_CONTENT)
    except Poll.DoesNotExist:
        logger.error(f"Poll {poll_id} not found")
        return Response({"message": "Poll not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Delete poll error: {str(e)}")
        return Response({"message": f"Failed to delete poll: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
@csrf_exempt
def delete_all_polls(request):
    try:
        email = request.data.get('email')
        user = AdminUser.objects.filter(email=email).order_by('-last_login').first()
        if not user or not user.last_login or (timezone.now() - user.last_login).total_seconds() > 3600:
            logger.error(f"Invalid or expired login for email: {email}")
            return Response({"message": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        
        Poll.objects.all().delete()
        logger.info(f"All polls deleted successfully by user: {user.email}")
        return Response({"message": "All polls deleted successfully!"}, status=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        logger.error(f"Failed to delete all polls: {str(e)}")
        return Response({"message": f"Failed to delete all polls: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import Newsletter, AdminUser, CurrentlyLoggedInUser
from .serializers import NewsletterSerializer
import logging
from django.utils import timezone
import cloudinary.uploader

logger = logging.getLogger(__name__)

class NewsletterViewSet(viewsets.ModelViewSet):
    queryset = Newsletter.objects.all()
    serializer_class = NewsletterSerializer
    permission_classes = []

    def get_queryset(self):
        try:
            # Return all newsletters regardless of authentication
            logger.info("Fetching all newsletters")
            return self.queryset.all()
        except Exception as e:
            logger.error(f"Failed to fetch newsletters: {str(e)}")
            return Newsletter.objects.none()

    def create(self, request, *args, **kwargs):
        try:
            # Get or create a default admin user for newsletter creation
            current_user = CurrentlyLoggedInUser.objects.first()
            if current_user:
                email = current_user.email
                user = AdminUser.objects.filter(email=email).order_by('-last_login').first()
            else:
                # If no logged in user, use the first admin user or create one
                user = AdminUser.objects.first()
                if not user:
                    logger.error("No admin user found in the system")
                    return Response({"message": "No admin user available"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            logger.info(f"Request POST data: {request.POST}")
            logger.info(f"Request FILES: {request.FILES}")
            serializer = self.get_serializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                newsletter = serializer.save(created_by=user)
                logger.info(f"Newsletter created successfully by user: {user.email}")
                return Response({
                    "message": "Newsletter created successfully!",
                    "data": serializer.data
                }, status=status.HTTP_201_CREATED)
            logger.error(f"Newsletter creation failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Failed to create newsletter: {str(e)}")
            return Response({"message": f"Failed to create newsletter: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request, *args, **kwargs):
        try:
            current_user = CurrentlyLoggedInUser.objects.first()
            if not current_user:
                logger.error("No currently logged-in user found")
                return Response({"message": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            
            email = current_user.email
            user = AdminUser.objects.filter(email=email).order_by('-last_login').first()
            if not user or not user.last_login or (timezone.now() - user.last_login).total_seconds() > 3600:
                logger.error(f"Invalid or expired login for email: {email}")
                CurrentlyLoggedInUser.objects.filter(email=email).delete()
                return Response({"message": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            logger.info(f"Request POST data: {request.POST}")
            logger.info(f"Request FILES: {request.FILES}")
            images_to_delete = request.POST.getlist('images_to_delete', [])
            serializer = self.get_serializer(instance, data=request.data, partial=partial, context={'request': request})
            if serializer.is_valid():
                newsletter = serializer.save()
                if images_to_delete:
                    for img_id in images_to_delete:
                        try:
                            img = NewsletterImage.objects.get(id=img_id, newsletter=newsletter)
                            img.delete()  # This will also delete the file from disk
                        except NewsletterImage.DoesNotExist:
                            logger.warning(f"Image {img_id} not found for newsletter {newsletter.id}")
                logger.info(f"Newsletter {newsletter.id} updated successfully by user: {user.email}")
                return Response({
                    "message": "Newsletter updated successfully!",
                    "data": serializer.data
                }, status=status.HTTP_200_OK)
            logger.error(f"Newsletter update failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Failed to update newsletter: {str(e)}")
            return Response({"message": f"Failed to update newsletter: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def destroy(self, request, *args, **kwargs):
        try:
            current_user = CurrentlyLoggedInUser.objects.first()
            if not current_user:
                logger.error("No currently logged-in user found")
                return Response({"message": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            
            email = current_user.email
            user = AdminUser.objects.filter(email=email).order_by('-last_login').first()
            if not user or not user.last_login or (timezone.now() - user.last_login).total_seconds() > 3600:
                logger.error(f"Invalid or expired login for email: {email}")
                CurrentlyLoggedInUser.objects.filter(email=email).delete()
                return Response({"message": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            
            instance = self.get_object()
            for img in instance.images.all():
                img.delete()  # This will also delete the file from disk
            self.perform_destroy(instance)
            logger.info(f"Newsletter {instance.id} deleted successfully by user: {user.email}")
            return Response({"message": "Newsletter deleted successfully!"}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Failed to delete newsletter: {str(e)}")
            return Response({"message": f"Failed to delete newsletter: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['delete'], url_path='images/(?P<image_id>\d+)')
    def delete_image(self, request, pk=None, image_id=None):
        try:
            current_user = CurrentlyLoggedInUser.objects.first()
            if not current_user:
                logger.error("No currently logged-in user found")
                return Response({"message": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            
            email = current_user.email
            user = AdminUser.objects.filter(email=email).order_by('-last_login').first()
            if not user or not user.last_login or (timezone.now() - user.last_login).total_seconds() > 3600:
                logger.error(f"Invalid or expired login for email: {email}")
                CurrentlyLoggedInUser.objects.filter(email=email).delete()
                return Response({"message": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            
            newsletter = self.get_object()
            try:
                img = NewsletterImage.objects.get(id=image_id, newsletter=newsletter)
                img.delete()  # This will also delete the file from disk
                logger.info(f"Image {image_id} deleted successfully from newsletter {newsletter.id}")
                return Response({"message": "Image deleted successfully!"}, status=status.HTTP_204_NO_CONTENT)
            except NewsletterImage.DoesNotExist:
                logger.warning(f"Image {image_id} not found for newsletter {newsletter.id}")
                return Response({"message": "Image not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Failed to delete image: {str(e)}")
            return Response({"message": f"Failed to delete image: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
@csrf_exempt
def delete_all_newsletters(request):
    try:
        current_user = CurrentlyLoggedInUser.objects.first()
        if not current_user:
            logger.error("No currently logged-in user found")
            return Response({"message": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        email = current_user.email
        user = AdminUser.objects.filter(email=email).order_by('-last_login').first()
        if not user or not user.last_login or (timezone.now() - user.last_login).total_seconds() > 3600:
            logger.error(f"Invalid or expired login for email: {email}")
            CurrentlyLoggedInUser.objects.filter(email=email).delete()
            return Response({"message": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

        for newsletter in Newsletter.objects.all():
            for img in newsletter.images.all():
                img.delete()  # This will also delete the file from disk

        Newsletter.objects.all().delete()
        logger.info(f"All newsletters deleted successfully by user: {user.email}")
        return Response({"message": "All newsletters deleted successfully!"}, status=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        logger.error(f"Failed to delete all newsletters: {str(e)}")
        return Response({"message": f"Failed to delete all newsletters: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


from .models import AdminUser, AdminOTP, Department, Degree, Student, Poll, CurrentlyLoggedInUser, Newsletter, SuccessStory, SuccessStoryImage
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from .serializers import DepartmentSerializer, DegreeSerializer, StudentSerializer, PollSerializer, PollCreateSerializer, VoteSerializer, NewsletterSerializer, SuccessStorySerializer, SuccessStoryImageSerializer
from rest_framework.views import APIView

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password, check_password
from django.views.decorators.http import require_http_methods
from django.contrib.auth import login
from django.middleware.csrf import get_token
import json
import logging
from .models import AdminUser, AdminOTP, Department, Degree, Student, Poll, CurrentlyLoggedInUser, Newsletter, SuccessStory, SuccessStoryImage
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from rest_framework.views import APIView
from django.utils import timezone
from .serializers import DepartmentSerializer, DegreeSerializer, StudentSerializer, PollSerializer, PollCreateSerializer, VoteSerializer, NewsletterSerializer, SuccessStorySerializer, SuccessStoryImageSerializer
import cloudinary.uploader
from cloudinary.utils import cloudinary_url

logger = logging.getLogger(__name__)




@api_view(['GET', 'POST'])
@csrf_exempt
def success_story_list_create(request):
    if request.method == 'GET':
        SuccessStory.objects.filter(expires_at__lte=timezone.now()).delete()
        stories = SuccessStory.objects.all().prefetch_related('images')
        serializer = SuccessStorySerializer(stories, many=True, context={'request': request})
        logger.info("Fetched all success stories")
        return Response(serializer.data, status=status.HTTP_200_OK)
    elif request.method == 'POST':
        try:
            current_user = CurrentlyLoggedInUser.objects.first()
            if not current_user:
                logger.error("No currently logged-in user found")
                return Response({"message": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            email = current_user.email
            user = AdminUser.objects.filter(email=email).order_by('-last_login').first()
            if not user or not user.last_login or (timezone.now() - user.last_login).total_seconds() > 3600:
                logger.error(f"Invalid or expired login for email: {email}")
                CurrentlyLoggedInUser.objects.filter(email=email).delete()
                return Response({"message": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            
            logger.info(f"Request POST data: {request.POST}")
            logger.info(f"Request FILES: {request.FILES}")
            
            data = request.POST.copy()
            data['created_by'] = str(user.id)
            data['expires_at'] = (timezone.now() + timezone.timedelta(days=365)).isoformat()
            
            images = request.FILES.getlist('images')
            serializer = SuccessStorySerializer(data=data, context={'created_by': user})
            if serializer.is_valid():
                story = serializer.save(created_by=user)
                for image in images:
                    try:
                        image_instance = SuccessStoryImage.objects.create(
                            success_story=story,
                            image=image
                        )
                        image_serializer = SuccessStoryImageSerializer(image_instance)
                    except Exception as e:
                        logger.error(f"Failed to save image: {str(e)}")
                        story.delete()
                        return Response({"message": f"Failed to save image: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                logger.info(f"Success story created successfully by user: {user.email}")
                return Response({
                    "message": "Success story created successfully!",
                    "data": SuccessStorySerializer(story, context={'request': request}).data
                }, status=status.HTTP_201_CREATED)
            logger.error(f"Success story creation failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Success story creation error: {str(e)}")
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
@csrf_exempt
def update_success_story(request, story_id):
    try:
        story = SuccessStory.objects.get(id=story_id)
        current_user = CurrentlyLoggedInUser.objects.first()
        if not current_user:
            logger.error("No currently logged-in user found")
            return Response({"message": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        email = current_user.email
        user = AdminUser.objects.filter(email=email).order_by('-last_login').first()
        if not user or not user.last_login or (timezone.now() - user.last_login).total_seconds() > 3600:
            logger.error(f"Invalid or expired login for email: {email}")
            CurrentlyLoggedInUser.objects.filter(email=email).delete()
            return Response({"message": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        
        logger.info(f"Request POST data: {request.POST}")
        logger.info(f"Request FILES: {request.FILES}")
        
        images = request.FILES.getlist('images')
        # Get list of image IDs to delete (if sent from frontend)
        images_to_delete = request.POST.getlist('images_to_delete', [])
        
        serializer = SuccessStorySerializer(story, data=request.POST, partial=True)
        if serializer.is_valid():
            story = serializer.save()
            
            # Delete specific images if requested
            if images_to_delete:
                for img_id in images_to_delete:
                    try:
                        img = SuccessStoryImage.objects.get(id=img_id, success_story=story)
                        img.delete()  # This will also delete the file from disk
                    except SuccessStoryImage.DoesNotExist:
                        logger.warning(f"Image {img_id} not found for story {story_id}")
            
            # Add new images if provided
            if images:
                for image in images:
                    try:
                        image_instance = SuccessStoryImage.objects.create(
                            success_story=story,
                            image=image
                        )
                        image_serializer = SuccessStoryImageSerializer(image_instance)
                    except Exception as e:
                        logger.error(f"Failed to save image: {str(e)}")
                        return Response({"message": f"Failed to save image: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            logger.info(f"Success story {story_id} updated successfully by user: {user.email}")
            return Response({
                "message": "Success story updated successfully!",
                "data": SuccessStorySerializer(story, context={'request': request}).data
            }, status=status.HTTP_200_OK)
        logger.error(f"Success story update failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except SuccessStory.DoesNotExist:
        logger.error(f"Success story {story_id} not found")
        return Response({"message": "Success story not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['DELETE'])
@csrf_exempt
def delete_success_story(request, story_id):
    try:
        story = SuccessStory.objects.get(id=story_id)
        current_user = CurrentlyLoggedInUser.objects.first()
        if not current_user:
            logger.error("No currently logged-in user found")
            return Response({"message": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        email = current_user.email
        user = AdminUser.objects.filter(email=email).order_by('-last_login').first()
        if not user or not user.last_login or (timezone.now() - user.last_login).total_seconds() > 3600:
            logger.error(f"Invalid or expired login for email: {email}")
            CurrentlyLoggedInUser.objects.filter(email=email).delete()
            return Response({"message": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        
        for img in story.images.all():
            img.delete()  # This will also delete the file from disk
        
        story.delete()
        logger.info(f"Success story {story_id} deleted successfully by user: {user.email}")
        return Response({"message": "Success story deleted successfully!"}, status=status.HTTP_204_NO_CONTENT)
    except SuccessStory.DoesNotExist:
        logger.error(f"Success story {story_id} not found")
        return Response({"message": "Success story not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['DELETE'])
@csrf_exempt
def delete_all_success_stories(request):
    try:
        current_user = CurrentlyLoggedInUser.objects.first()
        if not current_user:
            logger.error("No currently logged-in user found")
            return Response({"message": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        email = current_user.email
        user = AdminUser.objects.filter(email=email).order_by('-last_login').first()
        if not user or not user.last_login or (timezone.now() - user.last_login).total_seconds() > 3600:
            logger.error(f"Invalid or expired login for email: {email}")
            CurrentlyLoggedInUser.objects.filter(email=email).delete()
            return Response({"message": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        
        for story in SuccessStory.objects.all():
            for img in story.images.all():
                img.delete()  # This will also delete the file from disk
        
        SuccessStory.objects.all().delete()
        logger.info(f"All success stories deleted successfully by user: {user.email}")
        return Response({"message": "All success stories deleted successfully!"}, status=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        logger.error(f"Failed to delete all success stories: {str(e)}")
        return Response({"message": f"Failed to delete all success stories: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@csrf_exempt
def get_csrf_token(request):
    return JsonResponse({'csrfToken': get_token(request)})
    
from django.http import JsonResponse, HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Department, AlumniFeedback, Student, CurrentlyLoggedInUser, AdminUser
from .serializers import AlumniFeedbackSerializer
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

@api_view(['GET'])
def admin_feedback_list(request):
    logger.debug(f"Received GET request for /api/feedbacks/ with session data: {request.session}")
    current_user = CurrentlyLoggedInUser.objects.first()
    if not current_user:
        logger.error("admin_feedback_list: No currently logged-in user found")
        return Response({"message": "Authentication required. Please log in as an admin."}, status=status.HTTP_401_UNAUTHORIZED)
    
    email = current_user.email
    try:
        user = AdminUser.objects.get(email=email)
    except AdminUser.DoesNotExist:
        logger.error(f"admin_feedback_list: Admin user not found for email: {email}")
        return Response({"message": "Authentication required. Please log in as an admin."}, status=status.HTTP_401_UNAUTHORIZED)
    
    if not user.last_login or (timezone.now() - user.last_login).total_seconds() > 3600:
        logger.error(f"admin_feedback_list: Invalid or expired login for email: {email}")
        CurrentlyLoggedInUser.objects.filter(email=email).delete()
        return Response({"message": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        feedbacks = AlumniFeedback.objects.filter(for_admin=1)
        serializer = AlumniFeedbackSerializer(feedbacks, many=True)
        logger.info(f"admin_feedback_list: Fetched {len(serializer.data)} feedbacks for user={user.email}")
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"admin_feedback_list: Error fetching feedbacks: {str(e)}")
        return Response({"message": "Error fetching feedbacks"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
@csrf_exempt
def admin_feedback_detail(request, pk):
    logger.debug(f"Received PUT request for /api/feedbacks/{pk}/ with data: {request.data}")
    current_user = CurrentlyLoggedInUser.objects.first()
    if not current_user:
        logger.error("admin_feedback_detail: No currently logged-in user found")
        return Response({"message": "Authentication required. Please log in as an admin."}, status=status.HTTP_401_UNAUTHORIZED)
    
    email = current_user.email
    try:
        user = AdminUser.objects.get(email=email)
    except AdminUser.DoesNotExist:
        logger.error(f"admin_feedback_detail: Admin user not found for email: {email}")
        return Response({"message": "Authentication required. Please log in as an admin."}, status=status.HTTP_401_UNAUTHORIZED)
    
    if not user.last_login or (timezone.now() - user.last_login).total_seconds() > 3600:
        logger.error(f"admin_feedback_detail: Invalid or expired login for email: {email}")
        CurrentlyLoggedInUser.objects.filter(email=email).delete()
        return Response({"message": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        feedback = AlumniFeedback.objects.get(id=pk, for_admin=1)
    except AlumniFeedback.DoesNotExist:
        logger.error(f"admin_feedback_detail: Feedback not found: pk={pk}")
        return Response({"message": "Feedback not found"}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = AlumniFeedbackSerializer(feedback, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        logger.info(f"admin_feedback_detail: Feedback {pk} updated successfully by user={user.email}")
        return Response({
            "message": "Feedback updated successfully!",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
    logger.error(f"admin_feedback_detail: Validation failed: {serializer.errors}")
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@csrf_exempt
def admin_feedback_delete(request, pk):
    logger.debug(f"Received DELETE request for /api/feedbacks/{pk}/delete/ with data: {request.data}")
    current_user = CurrentlyLoggedInUser.objects.first()
    if not current_user:
        logger.error("admin_feedback_delete: No currently logged-in user found")
        return Response({"message": "Authentication required. Please log in as an admin."}, status=status.HTTP_401_UNAUTHORIZED)
    
    email = current_user.email
    try:
        user = AdminUser.objects.get(email=email)
    except AdminUser.DoesNotExist:
        logger.error(f"admin_feedback_delete: Admin user not found for email: {email}")
        return Response({"message": "Authentication required. Please log in as an admin."}, status=status.HTTP_401_UNAUTHORIZED)
    
    if not user.last_login or (timezone.now() - user.last_login).total_seconds() > 3600:
        logger.error(f"admin_feedback_delete: Invalid or expired login for email: {email}")
        CurrentlyLoggedInUser.objects.filter(email=email).delete()
        return Response({"message": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        feedback = AlumniFeedback.objects.get(id=pk, for_admin=1)
    except AlumniFeedback.DoesNotExist:
        logger.error(f"admin_feedback_delete: Feedback not found: pk={pk}")
        return Response({"message": "Feedback not found"}, status=status.HTTP_404_NOT_FOUND)
    
    feedback.delete()
    logger.info(f"admin_feedback_delete: Feedback {pk} deleted successfully by user={user.email}")
    return Response({"message": "Feedback deleted successfully!"}, status=status.HTTP_204_NO_CONTENT)

@api_view(['POST'])
@csrf_exempt
def admin_bulk_mark_read(request):
    logger.debug(f"Received POST request for /api/feedbacks/bulk-read/ with data: {request.data}")
    current_user = CurrentlyLoggedInUser.objects.first()
    if not current_user:
        logger.error("admin_bulk_mark_read: No currently logged-in user found")
        return Response({"message": "Authentication required. Please log in as an admin."}, status=status.HTTP_401_UNAUTHORIZED)
    
    email = current_user.email
    try:
        user = AdminUser.objects.get(email=email)
    except AdminUser.DoesNotExist:
        logger.error(f"admin_bulk_mark_read: Admin user not found for email: {email}")
        return Response({"message": "Authentication required. Please log in as an admin."}, status=status.HTTP_401_UNAUTHORIZED)
    
    if not user.last_login or (timezone.now() - user.last_login).total_seconds() > 3600:
        logger.error(f"admin_bulk_mark_read: Invalid or expired login for email: {email}")
        CurrentlyLoggedInUser.objects.filter(email=email).delete()
        return Response({"message": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
    
    ids = request.data.get('ids', [])
    if not ids:
        return Response({"message": "No IDs provided"}, status=status.HTTP_400_BAD_REQUEST)
    
    updated_count = AlumniFeedback.objects.filter(id__in=ids, for_admin=1).update(is_read=True)
    logger.info(f"admin_bulk_mark_read: Marked {updated_count} feedbacks as read by user={user.email}")
    return Response({"message": f"Marked {updated_count} feedbacks as read"}, status=status.HTTP_200_OK)

@api_view(['POST'])
@csrf_exempt
def admin_bulk_delete(request):
    logger.debug(f"Received POST request for /api/feedbacks/bulk-delete/ with data: {request.data}")
    current_user = CurrentlyLoggedInUser.objects.first()
    if not current_user:
        logger.error("admin_bulk_delete: No currently logged-in user found")
        return Response({"message": "Authentication required. Please log in as an admin."}, status=status.HTTP_401_UNAUTHORIZED)
    
    email = current_user.email
    try:
        user = AdminUser.objects.get(email=email)
    except AdminUser.DoesNotExist:
        logger.error(f"admin_bulk_delete: Admin user not found for email: {email}")
        return Response({"message": "Authentication required. Please log in as an admin."}, status=status.HTTP_401_UNAUTHORIZED)
    
    if not user.last_login or (timezone.now() - user.last_login).total_seconds() > 3600:
        logger.error(f"admin_bulk_delete: Invalid or expired login for email: {email}")
        CurrentlyLoggedInUser.objects.filter(email=email).delete()
        return Response({"message": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
    
    ids = request.data.get('ids', [])
    if not ids:
        return Response({"message": "No IDs provided"}, status=status.HTTP_400_BAD_REQUEST)
    
    deleted_count = AlumniFeedback.objects.filter(id__in=ids, for_admin=1).delete()[0]
    logger.info(f"admin_bulk_delete: Deleted {deleted_count} feedbacks by user={user.email}")
    return Response({"message": f"Deleted {deleted_count} feedbacks"}, status=status.HTTP_200_OK)