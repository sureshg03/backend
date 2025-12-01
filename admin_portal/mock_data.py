from django.db import transaction
from .models import Department, Degree, Student
import random

def generate_mock_data():
    tamil_names = [
        "Hari", "Gayathiri", "Suresh","Hari Gayathiri" "Sabari", "Saranya", "Karnika", "Avanith", "Vignesh", "Priya", "Arjun",
        "Kavya", "Ramesh", "Anitha", "Vijay", "Deepika", "Karthik", "Sneha", "Mohan", "Divya", "Santhosh",
        "Pavithra", "Rajesh", "Nisha", "Gowtham", "Shalini", "Praveen", "Meena", "Srinivas", "Aishwarya", "Balaji",
        "Keerthana", "Dinesh", "Lakshmi", "Vikram", "Swetha", "Aravind", "Pooja", "Sivakumar", "Janani", "Kiran",
        "Ramya", "Ashok", "Sindhu", "Vinoth", "Nandhini", "Siddharth", "Malathi", "Ravi", "Kavitha", "Manoj"
    ]

    job_titles = ["Software Engineer", "Data Analyst", "Product Manager", "DevOps Engineer", "UX Designer", "QA Engineer"]
    job_locations = ["Chennai", "Bangalore", "Coimbatore", "Hyderabad", "Pune", "Remote"]
    companies = ["TCS", "Infosys", "Wipro", "HCL", "Zoho", "Cognizant"]

    departments = [
        {"name": "Computer Science", "description": "Department of Computer Science and Engineering"},
        {"name": "Tamil", "description": "Department of Tamil Literature and Culture"},
        {"name": "Science", "description": "Department of General Sciences"},
    ]

    degrees = {
        "Computer Science": ["MCA", "MSc Computer Science", "MSc Data Science"],
        "Tamil": ["MA Tamil", "MPhil Tamil"],
        "Science": ["MSc Physics", "MSc Chemistry"],
    }

    with transaction.atomic():
        for dept_data in departments:
            dept = Department.objects.create(name=dept_data["name"], description=dept_data["description"])
            for degree_name in degrees[dept_data["name"]]:
                degree = Degree.objects.create(department=dept, name=degree_name, duration_years=2)
                for i in range(50):
                    Student.objects.create(
                        reg_no=f"REG{dept.id}{degree.id}{i:03d}",
                        name=random.choice(tamil_names),
                        email=f"{random.choice(tamil_names).lower()}{i}@example.com",
                        contact=f"+91{random.randint(6000000000, 9999999999)}",
                        degree=degree,
                        studying_year=random.choice(["I", "II"]),
                        graduation_year=random.randint(2023, 2026),
                        job_title=random.choice(job_titles) if random.random() > 0.3 else "",
                        job_location=random.choice(job_locations) if random.random() > 0.3 else "",
                        previous_company=random.choice(companies) if random.random() > 0.5 else ""
                    )

if __name__ == "__main__":
    generate_mock_data()