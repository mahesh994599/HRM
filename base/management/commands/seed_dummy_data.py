"""
Management command to seed dummy data for all HRM modules.
Usage: python manage.py seed_dummy_data
"""

import random
from datetime import date, datetime, time, timedelta
from types import SimpleNamespace

from django.apps import apps
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from horilla import horilla_middlewares

from base.models import (
    Company,
    Department,
    EmployeeShift,
    EmployeeShiftDay,
    EmployeeShiftSchedule,
    EmployeeType,
    JobPosition,
    JobRole,
    WorkType,
)
from employee.models import Employee, EmployeeBankDetails, EmployeeWorkInformation


class Command(BaseCommand):
    help = "Seed the database with realistic dummy data for all HRM modules"

    def handle(self, *args, **options):
        self.stdout.write("Seeding dummy data...")

        # Set up a fake request context for models that access request.session
        admin_user = User.objects.filter(is_superuser=True).first()
        fake_session = {"selected_company": "all"}
        fake_request = SimpleNamespace(
            session=fake_session,
            POST={},
            META={"QUERY_STRING": ""},
            user=admin_user,
            working_employees=None,
            path="/",
            build_absolute_uri=lambda x="/": "http://localhost:8000/",
        )
        horilla_middlewares._thread_locals.request = fake_request

        company = self._create_company()
        departments = self._create_departments(company)
        positions = self._create_job_positions(departments, company)
        roles = self._create_job_roles(positions, company)
        work_types = self._create_work_types(company)
        emp_types = self._create_employee_types(company)
        shift, shift_days = self._create_shifts(company)
        employees = self._create_employees(
            company, departments, positions, roles, work_types, emp_types, shift
        )
        self._create_bank_details(employees)

        if apps.is_installed("leave"):
            self._create_leave_data(employees)

        if apps.is_installed("attendance"):
            self._create_attendance_data(employees, shift, shift_days)

        if apps.is_installed("payroll"):
            self._create_payroll_data(employees, company, departments)

        if apps.is_installed("recruitment"):
            self._create_recruitment_data(company, positions, employees)

        if apps.is_installed("pms"):
            self._create_performance_data(employees, company)

        if apps.is_installed("asset"):
            self._create_asset_data(employees, company)

        if apps.is_installed("helpdesk"):
            self._create_helpdesk_data(employees, company, departments)

        if apps.is_installed("project"):
            self._create_project_data(employees, company)

        if apps.is_installed("offboarding"):
            self._create_offboarding_data(employees, company)

        self.stdout.write(self.style.SUCCESS("Dummy data seeded successfully!"))

    def _create_company(self):
        company, created = Company.objects.get_or_create(
            company="Synergific Technologies",
            defaults={
                "hq": True,
                "address": "42 Innovation Drive, Whitefield",
                "country": "India",
                "state": "Karnataka",
                "city": "Bangalore",
                "zip": "560066",
            },
        )
        action = "Created" if created else "Already exists"
        self.stdout.write(f"  {action}: Company '{company}'")
        return company

    def _create_departments(self, company):
        dept_names = [
            "Engineering",
            "Human Resources",
            "Marketing",
            "Finance",
            "Operations",
        ]
        departments = {}
        for name in dept_names:
            try:
                dept = Department.objects.get(department=name)
            except Department.DoesNotExist:
                dept = Department(department=name)
                dept.save()
            dept.company_id.add(company)
            departments[name] = dept
        self.stdout.write(f"  Created {len(departments)} departments")
        return departments

    def _create_job_positions(self, departments, company):
        position_map = {
            "Engineering": [
                "Software Engineer",
                "Senior Software Engineer",
                "Tech Lead",
            ],
            "Human Resources": ["HR Manager", "HR Executive"],
            "Marketing": ["Marketing Manager", "Content Specialist"],
            "Finance": ["Finance Manager", "Accountant"],
            "Operations": ["Operations Manager", "Office Administrator"],
        }
        positions = {}
        for dept_name, pos_list in position_map.items():
            for pos_name in pos_list:
                try:
                    pos = JobPosition.objects.get(
                        job_position=pos_name,
                        department_id=departments[dept_name],
                    )
                except JobPosition.DoesNotExist:
                    pos = JobPosition(
                        job_position=pos_name,
                        department_id=departments[dept_name],
                    )
                    pos.save()
                pos.company_id.add(company)
                positions[pos_name] = pos
        self.stdout.write(f"  Created {len(positions)} job positions")
        return positions

    def _create_job_roles(self, positions, company):
        role_map = {
            "Software Engineer": [
                "Frontend Developer",
                "Backend Developer",
                "Full Stack Developer",
            ],
            "Senior Software Engineer": [
                "Senior Frontend Developer",
                "Senior Backend Developer",
            ],
            "Tech Lead": ["Engineering Lead"],
            "HR Manager": ["HR Lead"],
            "HR Executive": ["Recruitment Specialist", "Payroll Specialist"],
            "Marketing Manager": ["Digital Marketing Lead"],
            "Content Specialist": ["Content Writer", "SEO Specialist"],
            "Finance Manager": ["Finance Lead"],
            "Accountant": ["Accounts Executive"],
            "Operations Manager": ["Operations Lead"],
            "Office Administrator": ["Admin Executive"],
        }
        roles = {}
        for pos_name, role_list in role_map.items():
            if pos_name in positions:
                for role_name in role_list:
                    try:
                        role = JobRole.objects.get(
                            job_position_id=positions[pos_name],
                            job_role=role_name,
                        )
                    except JobRole.DoesNotExist:
                        role = JobRole(
                            job_position_id=positions[pos_name],
                            job_role=role_name,
                        )
                        role.save()
                    role.company_id.add(company)
                    roles[role_name] = role
        self.stdout.write(f"  Created {len(roles)} job roles")
        return roles

    def _create_work_types(self, company):
        wt_names = ["On-Site", "Remote", "Hybrid"]
        work_types = {}
        for name in wt_names:
            try:
                wt = WorkType.objects.get(work_type=name)
            except WorkType.DoesNotExist:
                wt = WorkType(work_type=name)
                wt.save()
            wt.company_id.add(company)
            work_types[name] = wt
        self.stdout.write(f"  Created {len(work_types)} work types")
        return work_types

    def _create_employee_types(self, company):
        et_names = ["Full-time", "Part-time", "Contract"]
        emp_types = {}
        for name in et_names:
            try:
                et = EmployeeType.objects.get(employee_type=name)
            except EmployeeType.DoesNotExist:
                et = EmployeeType(employee_type=name)
                et.save()
            et.company_id.add(company)
            emp_types[name] = et
        self.stdout.write(f"  Created {len(emp_types)} employee types")
        return emp_types

    def _create_shifts(self, company):
        # Create shift days
        day_names = [
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        ]
        shift_days = {}
        for day in day_names:
            sd, created = EmployeeShiftDay.objects.get_or_create(day=day)
            sd.company_id.add(company)
            shift_days[day] = sd

        # Create day shift
        try:
            shift = EmployeeShift.objects.get(employee_shift="Day Shift")
        except EmployeeShift.DoesNotExist:
            shift = EmployeeShift(
                employee_shift="Day Shift",
                weekly_full_time="40:00",
                full_time="200:00",
            )
            shift.save()
        shift.company_id.add(company)

        # Create schedule for Mon-Fri
        weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday"]
        for day in weekdays:
            if not EmployeeShiftSchedule.objects.filter(
                day=shift_days[day], shift_id=shift
            ).exists():
                schedule = EmployeeShiftSchedule(
                    day=shift_days[day],
                    shift_id=shift,
                    minimum_working_hour="08:00",
                    start_time=time(9, 0),
                    end_time=time(18, 0),
                )
                schedule.save()

        self.stdout.write(f"  Created shift: Day Shift (Mon-Fri, 9:00-18:00)")
        return shift, shift_days

    def _create_employees(
        self, company, departments, positions, roles, work_types, emp_types, shift
    ):
        employee_data = [
            {
                "first": "Arjun",
                "last": "Mehta",
                "email": "arjun.mehta@synergific.com",
                "phone": "9876543210",
                "gender": "male",
                "dob": date(1988, 3, 15),
                "dept": "Engineering",
                "position": "Tech Lead",
                "role": "Engineering Lead",
                "work_type": "Hybrid",
                "emp_type": "Full-time",
                "salary": 180000,
                "joining": date(2021, 1, 10),
                "manager": None,
            },
            {
                "first": "Priya",
                "last": "Sharma",
                "email": "priya.sharma@synergific.com",
                "phone": "9876543211",
                "gender": "female",
                "dob": date(1990, 7, 22),
                "dept": "Engineering",
                "position": "Senior Software Engineer",
                "role": "Senior Backend Developer",
                "work_type": "Remote",
                "emp_type": "Full-time",
                "salary": 140000,
                "joining": date(2021, 6, 1),
                "manager": "arjun.mehta@synergific.com",
            },
            {
                "first": "Rahul",
                "last": "Kumar",
                "email": "rahul.kumar@synergific.com",
                "phone": "9876543212",
                "gender": "male",
                "dob": date(1992, 11, 5),
                "dept": "Engineering",
                "position": "Senior Software Engineer",
                "role": "Senior Frontend Developer",
                "work_type": "On-Site",
                "emp_type": "Full-time",
                "salary": 135000,
                "joining": date(2022, 2, 15),
                "manager": "arjun.mehta@synergific.com",
            },
            {
                "first": "Sneha",
                "last": "Iyer",
                "email": "sneha.iyer@synergific.com",
                "phone": "9876543213",
                "gender": "female",
                "dob": date(1995, 1, 30),
                "dept": "Engineering",
                "position": "Software Engineer",
                "role": "Backend Developer",
                "work_type": "Remote",
                "emp_type": "Full-time",
                "salary": 90000,
                "joining": date(2023, 3, 20),
                "manager": "priya.sharma@synergific.com",
            },
            {
                "first": "Vikram",
                "last": "Patel",
                "email": "vikram.patel@synergific.com",
                "phone": "9876543214",
                "gender": "male",
                "dob": date(1994, 5, 12),
                "dept": "Engineering",
                "position": "Software Engineer",
                "role": "Frontend Developer",
                "work_type": "Hybrid",
                "emp_type": "Full-time",
                "salary": 85000,
                "joining": date(2023, 7, 3),
                "manager": "rahul.kumar@synergific.com",
            },
            {
                "first": "Ananya",
                "last": "Reddy",
                "email": "ananya.reddy@synergific.com",
                "phone": "9876543215",
                "gender": "female",
                "dob": date(1996, 9, 18),
                "dept": "Engineering",
                "position": "Software Engineer",
                "role": "Full Stack Developer",
                "work_type": "On-Site",
                "emp_type": "Contract",
                "salary": 75000,
                "joining": date(2024, 1, 8),
                "manager": "priya.sharma@synergific.com",
            },
            {
                "first": "Deepa",
                "last": "Nair",
                "email": "deepa.nair@synergific.com",
                "phone": "9876543216",
                "gender": "female",
                "dob": date(1987, 12, 2),
                "dept": "Human Resources",
                "position": "HR Manager",
                "role": "HR Lead",
                "work_type": "On-Site",
                "emp_type": "Full-time",
                "salary": 120000,
                "joining": date(2020, 8, 15),
                "manager": None,
            },
            {
                "first": "Karthik",
                "last": "Srinivasan",
                "email": "karthik.s@synergific.com",
                "phone": "9876543217",
                "gender": "male",
                "dob": date(1993, 4, 25),
                "dept": "Human Resources",
                "position": "HR Executive",
                "role": "Recruitment Specialist",
                "work_type": "On-Site",
                "emp_type": "Full-time",
                "salary": 65000,
                "joining": date(2022, 11, 1),
                "manager": "deepa.nair@synergific.com",
            },
            {
                "first": "Meera",
                "last": "Joshi",
                "email": "meera.joshi@synergific.com",
                "phone": "9876543218",
                "gender": "female",
                "dob": date(1991, 6, 14),
                "dept": "Marketing",
                "position": "Marketing Manager",
                "role": "Digital Marketing Lead",
                "work_type": "Hybrid",
                "emp_type": "Full-time",
                "salary": 110000,
                "joining": date(2021, 4, 5),
                "manager": None,
            },
            {
                "first": "Aditya",
                "last": "Gupta",
                "email": "aditya.gupta@synergific.com",
                "phone": "9876543219",
                "gender": "male",
                "dob": date(1997, 2, 28),
                "dept": "Marketing",
                "position": "Content Specialist",
                "role": "Content Writer",
                "work_type": "Remote",
                "emp_type": "Part-time",
                "salary": 45000,
                "joining": date(2024, 6, 10),
                "manager": "meera.joshi@synergific.com",
            },
            {
                "first": "Ravi",
                "last": "Krishnan",
                "email": "ravi.krishnan@synergific.com",
                "phone": "9876543220",
                "gender": "male",
                "dob": date(1985, 8, 7),
                "dept": "Finance",
                "position": "Finance Manager",
                "role": "Finance Lead",
                "work_type": "On-Site",
                "emp_type": "Full-time",
                "salary": 130000,
                "joining": date(2020, 3, 1),
                "manager": None,
            },
            {
                "first": "Lakshmi",
                "last": "Venkatesh",
                "email": "lakshmi.v@synergific.com",
                "phone": "9876543221",
                "gender": "female",
                "dob": date(1993, 10, 20),
                "dept": "Finance",
                "position": "Accountant",
                "role": "Accounts Executive",
                "work_type": "On-Site",
                "emp_type": "Full-time",
                "salary": 70000,
                "joining": date(2023, 1, 15),
                "manager": "ravi.krishnan@synergific.com",
            },
            {
                "first": "Suresh",
                "last": "Babu",
                "email": "suresh.babu@synergific.com",
                "phone": "9876543222",
                "gender": "male",
                "dob": date(1986, 5, 30),
                "dept": "Operations",
                "position": "Operations Manager",
                "role": "Operations Lead",
                "work_type": "On-Site",
                "emp_type": "Full-time",
                "salary": 115000,
                "joining": date(2020, 11, 20),
                "manager": None,
            },
            {
                "first": "Divya",
                "last": "Menon",
                "email": "divya.menon@synergific.com",
                "phone": "9876543223",
                "gender": "female",
                "dob": date(1998, 3, 8),
                "dept": "Operations",
                "position": "Office Administrator",
                "role": "Admin Executive",
                "work_type": "On-Site",
                "emp_type": "Full-time",
                "salary": 50000,
                "joining": date(2024, 4, 1),
                "manager": "suresh.babu@synergific.com",
            },
            {
                "first": "Nikhil",
                "last": "Desai",
                "email": "nikhil.desai@synergific.com",
                "phone": "9876543224",
                "gender": "male",
                "dob": date(1995, 7, 19),
                "dept": "Engineering",
                "position": "Software Engineer",
                "role": "Backend Developer",
                "work_type": "Hybrid",
                "emp_type": "Full-time",
                "salary": 88000,
                "joining": date(2023, 9, 11),
                "manager": "priya.sharma@synergific.com",
            },
        ]

        employees = {}
        # First pass: create all employees
        for data in employee_data:
            if Employee.objects.filter(email=data["email"]).exists():
                emp = Employee.objects.get(email=data["email"])
                employees[data["email"]] = emp
                continue

            emp = Employee(
                employee_first_name=data["first"],
                employee_last_name=data["last"],
                email=data["email"],
                phone=data["phone"],
                gender=data["gender"],
                dob=data["dob"],
                marital_status=random.choice(["single", "married"]),
                address=f"{random.randint(1,200)}, {random.choice(['MG Road','Brigade Road','Koramangala','Indiranagar','HSR Layout'])}, Bangalore",
                country="India",
                state="Karnataka",
                city="Bangalore",
                zip="560066",
            )
            emp.save()
            employees[data["email"]] = emp

        # Second pass: update work info with departments, positions, roles, managers
        for data in employee_data:
            emp = employees[data["email"]]
            work_info = emp.employee_work_info

            work_info.company_id = company
            work_info.department_id = departments[data["dept"]]
            work_info.job_position_id = positions[data["position"]]
            work_info.job_role_id = roles[data["role"]]
            work_info.shift_id = shift
            work_info.work_type_id = work_types[data["work_type"]]
            work_info.employee_type_id = emp_types[data["emp_type"]]
            work_info.date_joining = data["joining"]
            work_info.basic_salary = data["salary"]
            work_info.salary_hour = data["salary"] // 160
            work_info.email = data["email"]
            work_info.location = "Bangalore"

            if data["manager"] and data["manager"] in employees:
                work_info.reporting_manager_id = employees[data["manager"]]

            work_info.save()

        self.stdout.write(f"  Created {len(employees)} employees with work info")
        return employees

    def _create_bank_details(self, employees):
        banks = [
            ("State Bank of India", "SBIN0001234"),
            ("HDFC Bank", "HDFC0002345"),
            ("ICICI Bank", "ICIC0003456"),
            ("Axis Bank", "UTIB0004567"),
            ("Kotak Mahindra Bank", "KKBK0005678"),
        ]
        count = 0
        for email, emp in employees.items():
            if EmployeeBankDetails.objects.filter(employee_id=emp).exists():
                continue
            bank_name, ifsc = random.choice(banks)
            bank = EmployeeBankDetails(
                employee_id=emp,
                bank_name=bank_name,
                account_number=f"{random.randint(10000000000, 99999999999)}",
                branch="Bangalore Main Branch",
                address="MG Road, Bangalore",
                country="India",
                state="Karnataka",
                city="Bangalore",
                any_other_code1=ifsc,
            )
            bank.save()
            count += 1
        self.stdout.write(f"  Created {count} bank detail records")

    def _create_leave_data(self, employees):
        from leave.models import AvailableLeave, LeaveRequest, LeaveType

        leave_types_data = [
            {
                "name": "Casual Leave",
                "color": "#6366F1",
                "payment": "paid",
                "total_days": 12,
                "reset": True,
                "reset_based": "yearly",
                "reset_month": "1",
                "reset_day": "1",
            },
            {
                "name": "Sick Leave",
                "color": "#EF4444",
                "payment": "paid",
                "total_days": 10,
                "reset": True,
                "reset_based": "yearly",
                "reset_month": "1",
                "reset_day": "1",
            },
            {
                "name": "Earned Leave",
                "color": "#10B981",
                "payment": "paid",
                "total_days": 15,
                "reset": True,
                "reset_based": "yearly",
                "reset_month": "1",
                "reset_day": "1",
            },
            {
                "name": "Loss of Pay",
                "color": "#F59E0B",
                "payment": "unpaid",
                "total_days": 365,
                "reset": False,
            },
        ]

        leave_types = {}
        for lt_data in leave_types_data:
            try:
                lt = LeaveType.objects.get(name=lt_data["name"])
            except LeaveType.DoesNotExist:
                lt = LeaveType(**lt_data)
                lt.save()
            leave_types[lt_data["name"]] = lt
        self.stdout.write(f"  Created {len(leave_types)} leave types")

        # Assign available leaves to all employees
        count = 0
        for email, emp in employees.items():
            for lt_name, lt in leave_types.items():
                if lt_name == "Loss of Pay":
                    continue
                if not AvailableLeave.objects.filter(
                    employee_id=emp, leave_type_id=lt
                ).exists():
                    avail = AvailableLeave(
                        employee_id=emp,
                        leave_type_id=lt,
                        available_days=lt.total_days,
                        total_leave_days=0,
                    )
                    avail.save()
                    count += 1
        self.stdout.write(f"  Assigned {count} leave balances")

        # Create sample leave requests
        today = date.today()
        emp_list = list(employees.values())
        leave_requests = [
            {
                "employee": emp_list[3],
                "leave_type": "Casual Leave",
                "start": today - timedelta(days=20),
                "end": today - timedelta(days=18),
                "status": "approved",
                "desc": "Family function",
            },
            {
                "employee": emp_list[4],
                "leave_type": "Sick Leave",
                "start": today - timedelta(days=10),
                "end": today - timedelta(days=9),
                "status": "approved",
                "desc": "Fever and cold",
            },
            {
                "employee": emp_list[1],
                "leave_type": "Casual Leave",
                "start": today + timedelta(days=5),
                "end": today + timedelta(days=7),
                "status": "requested",
                "desc": "Vacation trip",
            },
            {
                "employee": emp_list[7],
                "leave_type": "Earned Leave",
                "start": today + timedelta(days=15),
                "end": today + timedelta(days=19),
                "status": "requested",
                "desc": "Hometown visit",
            },
            {
                "employee": emp_list[9],
                "leave_type": "Casual Leave",
                "start": today - timedelta(days=5),
                "end": today - timedelta(days=5),
                "status": "rejected",
                "desc": "Personal work",
            },
            {
                "employee": emp_list[11],
                "leave_type": "Sick Leave",
                "start": today - timedelta(days=3),
                "end": today - timedelta(days=2),
                "status": "approved",
                "desc": "Doctor appointment and rest",
            },
            {
                "employee": emp_list[5],
                "leave_type": "Casual Leave",
                "start": today + timedelta(days=10),
                "end": today + timedelta(days=11),
                "status": "requested",
                "desc": "Wedding ceremony",
            },
            {
                "employee": emp_list[14],
                "leave_type": "Sick Leave",
                "start": today - timedelta(days=15),
                "end": today - timedelta(days=14),
                "status": "approved",
                "desc": "Not feeling well",
            },
        ]

        lr_count = 0
        for lr_data in leave_requests:
            if not LeaveRequest.objects.filter(
                employee_id=lr_data["employee"],
                start_date=lr_data["start"],
                leave_type_id=leave_types[lr_data["leave_type"]],
            ).exists():
                days = (lr_data["end"] - lr_data["start"]).days + 1
                lr = LeaveRequest(
                    employee_id=lr_data["employee"],
                    leave_type_id=leave_types[lr_data["leave_type"]],
                    start_date=lr_data["start"],
                    end_date=lr_data["end"],
                    requested_days=days,
                    description=lr_data["desc"],
                    status=lr_data["status"],
                )
                lr.save()
                lr_count += 1
        self.stdout.write(f"  Created {lr_count} leave requests")

    def _create_attendance_data(self, employees, shift, shift_days):
        from attendance.models import Attendance, AttendanceActivity

        today = date.today()
        day_map = {
            0: "monday",
            1: "tuesday",
            2: "wednesday",
            3: "thursday",
            4: "friday",
            5: "saturday",
            6: "sunday",
        }
        emp_list = list(employees.values())
        att_count = 0

        for day_offset in range(30, 0, -1):
            d = today - timedelta(days=day_offset)
            weekday = d.weekday()

            # Skip weekends
            if weekday >= 5:
                continue

            day_name = day_map[weekday]
            shift_day = shift_days.get(day_name)

            for emp in emp_list:
                if Attendance.objects.filter(
                    employee_id=emp, attendance_date=d
                ).exists():
                    continue

                # Random clock in between 8:45 and 9:30
                clock_in_hour = 9
                clock_in_min = random.randint(0, 30)
                if random.random() < 0.3:
                    clock_in_hour = 8
                    clock_in_min = random.randint(45, 59)

                clock_in = time(clock_in_hour, clock_in_min)

                # Random clock out between 17:30 and 19:00
                clock_out_hour = random.choice([17, 18])
                clock_out_min = random.randint(0, 59)
                if clock_out_hour == 17:
                    clock_out_min = random.randint(30, 59)
                clock_out = time(clock_out_hour, clock_out_min)

                # Calculate worked hours
                cin = datetime.combine(d, clock_in)
                cout = datetime.combine(d, clock_out)
                worked_seconds = (cout - cin).total_seconds()
                hours = int(worked_seconds // 3600)
                minutes = int((worked_seconds % 3600) // 60)
                worked_str = f"{hours:02d}:{minutes:02d}"

                # Calculate overtime (over 8 hours)
                overtime_seconds = max(0, worked_seconds - 8 * 3600)
                ot_hours = int(overtime_seconds // 3600)
                ot_minutes = int((overtime_seconds % 3600) // 60)
                overtime_str = f"{ot_hours:02d}:{ot_minutes:02d}"

                att = Attendance(
                    employee_id=emp,
                    attendance_date=d,
                    shift_id=shift,
                    work_type_id=emp.employee_work_info.work_type_id,
                    attendance_day=shift_day,
                    attendance_clock_in_date=d,
                    attendance_clock_in=clock_in,
                    attendance_clock_out_date=d,
                    attendance_clock_out=clock_out,
                    attendance_worked_hour=worked_str,
                    minimum_hour="08:00",
                    attendance_overtime=overtime_str,
                )
                att.save()

                # Create activity record
                activity = AttendanceActivity(
                    employee_id=emp,
                    attendance_date=d,
                    shift_day=shift_day,
                    clock_in_date=d,
                    clock_in=clock_in,
                    clock_out_date=d,
                    clock_out=clock_out,
                )
                activity.save()
                att_count += 1

        self.stdout.write(f"  Created {att_count} attendance records (last 30 days)")

    def _create_payroll_data(self, employees, company, departments):
        from payroll.models.models import Allowance, Contract, Deduction
        from payroll.models.tax_models import FilingStatus

        # Create filing status
        try:
            filing = FilingStatus.objects.get(filing_status="Standard")
        except FilingStatus.DoesNotExist:
            filing = FilingStatus(
                filing_status="Standard",
                based_on="taxable_gross_pay",
            )
            filing.save()
        self.stdout.write("  Created filing status")

        # Create contracts
        count = 0
        for email, emp in employees.items():
            if Contract.objects.filter(
                employee_id=emp, contract_status="active"
            ).exists():
                continue

            work_info = emp.employee_work_info
            contract = Contract(
                contract_name=f"{emp.get_full_name()} - Employment Contract",
                employee_id=emp,
                contract_start_date=work_info.date_joining or date(2024, 1, 1),
                wage_type="monthly",
                pay_frequency="monthly",
                wage=work_info.basic_salary or 50000,
                contract_status="active",
                department=work_info.department_id,
                filing_status=filing,
            )
            contract.save()
            count += 1
        self.stdout.write(f"  Created {count} payroll contracts")

        # Create allowances
        allowances_data = [
            {
                "title": "House Rent Allowance",
                "is_fixed": False,
                "based_on": "basic_pay",
                "rate": 40.0,
                "is_taxable": True,
                "include_active_employees": True,
            },
            {
                "title": "Transport Allowance",
                "is_fixed": True,
                "amount": 3000.0,
                "is_taxable": False,
                "include_active_employees": True,
            },
            {
                "title": "Medical Allowance",
                "is_fixed": True,
                "amount": 1500.0,
                "is_taxable": False,
                "include_active_employees": True,
            },
            {
                "title": "Special Allowance",
                "is_fixed": False,
                "based_on": "basic_pay",
                "rate": 10.0,
                "is_taxable": True,
                "include_active_employees": True,
            },
        ]
        a_count = 0
        for a_data in allowances_data:
            if not Allowance.objects.filter(title=a_data["title"]).exists():
                allowance = Allowance(**a_data)
                allowance.save()
                a_count += 1
        self.stdout.write(f"  Created {a_count} allowances")

        # Create deductions
        deductions_data = [
            {
                "title": "Provident Fund (PF)",
                "is_fixed": False,
                "based_on": "basic_pay",
                "rate": 12.0,
                "employer_rate": 12.0,
                "is_pretax": True,
                "include_active_employees": True,
            },
            {
                "title": "Professional Tax",
                "is_fixed": True,
                "amount": 200.0,
                "is_pretax": True,
                "include_active_employees": True,
            },
            {
                "title": "ESI",
                "is_fixed": False,
                "based_on": "gross_pay",
                "rate": 0.75,
                "employer_rate": 3.25,
                "is_pretax": True,
                "include_active_employees": True,
            },
        ]
        d_count = 0
        for d_data in deductions_data:
            if not Deduction.objects.filter(title=d_data["title"]).exists():
                deduction = Deduction(**d_data)
                deduction.save()
                d_count += 1
        self.stdout.write(f"  Created {d_count} deductions")

    def _create_recruitment_data(self, company, positions, employees):
        from recruitment.models import Recruitment, Skill

        skills_data = [
            "Python",
            "JavaScript",
            "React",
            "Django",
            "Node.js",
            "AWS",
            "Docker",
            "SQL",
            "TypeScript",
            "Git",
        ]
        skills = {}
        for s in skills_data:
            try:
                skill = Skill.objects.get(title=s)
            except Skill.DoesNotExist:
                skill = Skill(title=s)
                skill.save()
            skills[s] = skill

        emp_list = list(employees.values())
        # Find managers for recruitment
        managers = [e for e in emp_list if e.employee_work_info.reporting_manager_id is None]
        if not managers:
            managers = emp_list[:2]

        recruitments = [
            {
                "title": "Senior Backend Developer Hiring",
                "position": "Senior Software Engineer",
                "vacancy": 2,
                "skills": ["Python", "Django", "AWS", "Docker", "SQL"],
                "desc": "Looking for experienced backend developers to join our growing engineering team.",
            },
            {
                "title": "Marketing Manager Recruitment",
                "position": "Marketing Manager",
                "vacancy": 1,
                "skills": ["JavaScript", "React"],
                "desc": "Seeking a dynamic marketing manager to lead our digital marketing initiatives.",
            },
        ]

        count = 0
        for r_data in recruitments:
            if Recruitment.objects.filter(title=r_data["title"]).exists():
                continue
            rec = Recruitment(
                title=r_data["title"],
                company_id=company,
                vacancy=r_data["vacancy"],
                description=r_data["desc"],
                start_date=date.today() - timedelta(days=10),
                end_date=date.today() + timedelta(days=50),
            )
            rec.save()
            rec.open_positions.add(positions[r_data["position"]])
            rec.recruitment_managers.set(managers[:2])
            for s_name in r_data["skills"]:
                if s_name in skills:
                    rec.skills.add(skills[s_name])
            count += 1

        self.stdout.write(f"  Created {count} recruitment postings")

    def _create_performance_data(self, employees, company):
        from pms.models import (
            EmployeeKeyResult,
            EmployeeObjective,
            Feedback,
            KeyResult,
            Objective,
            Period,
            Question,
            QuestionTemplate,
        )

        today = date.today()
        emp_list = list(employees.values())
        managers = [
            e
            for e in emp_list
            if e.employee_work_info.reporting_manager_id is None
        ]

        # Create period
        try:
            period = Period.objects.get(period_name="Q2 2026")
        except Period.DoesNotExist:
            period = Period(
                period_name="Q2 2026",
                start_date=date(2026, 4, 1),
                end_date=date(2026, 6, 30),
            )
            period.save()
            period.company_id.add(company)
        self.stdout.write("  Created performance period")

        # Create key results
        kr_data = [
            {
                "title": "Code Quality Score",
                "description": "Maintain code quality score above 90% in SonarQube",
                "progress_type": "%",
                "target_value": 100,
            },
            {
                "title": "Sprint Velocity",
                "description": "Achieve average sprint velocity of 40 story points",
                "progress_type": "#",
                "target_value": 40,
            },
            {
                "title": "Customer Satisfaction",
                "description": "Maintain customer satisfaction rating above 4.5",
                "progress_type": "#",
                "target_value": 5,
            },
            {
                "title": "Revenue Target",
                "description": "Achieve quarterly revenue target",
                "progress_type": "%",
                "target_value": 100,
            },
            {
                "title": "Employee Retention",
                "description": "Maintain employee retention rate above 95%",
                "progress_type": "%",
                "target_value": 100,
            },
            {
                "title": "Training Hours",
                "description": "Complete 20 hours of professional development training",
                "progress_type": "#",
                "target_value": 20,
            },
        ]
        key_results = {}
        for kr in kr_data:
            try:
                k = KeyResult.objects.get(title=kr["title"])
            except KeyResult.DoesNotExist:
                k = KeyResult(company_id=company, **kr)
                k.save()
            key_results[kr["title"]] = k
        self.stdout.write(f"  Created {len(key_results)} key results")

        # Create objectives
        obj_data = [
            {
                "title": "Improve Engineering Excellence",
                "description": "Drive engineering best practices and code quality across the team",
                "duration_unit": "months",
                "duration": 3,
                "krs": ["Code Quality Score", "Sprint Velocity"],
            },
            {
                "title": "Boost Customer Satisfaction",
                "description": "Improve customer experience and satisfaction metrics",
                "duration_unit": "months",
                "duration": 3,
                "krs": ["Customer Satisfaction", "Revenue Target"],
            },
            {
                "title": "Strengthen Team Culture",
                "description": "Build a strong, inclusive, and high-performing team culture",
                "duration_unit": "months",
                "duration": 3,
                "krs": ["Employee Retention", "Training Hours"],
            },
        ]
        objectives = {}
        for o in obj_data:
            krs = o.pop("krs")
            try:
                obj = Objective.objects.get(title=o["title"])
            except Objective.DoesNotExist:
                obj = Objective(company_id=company, **o)
                obj.save()
                for kr_name in krs:
                    obj.key_result_id.add(key_results[kr_name])
                if managers:
                    obj.managers.add(managers[0])
            objectives[obj.title] = obj
        self.stdout.write(f"  Created {len(objectives)} objectives")

        # Assign objectives to employees
        eo_count = 0
        assignments = [
            (emp_list[1], "Improve Engineering Excellence"),
            (emp_list[2], "Improve Engineering Excellence"),
            (emp_list[3], "Improve Engineering Excellence"),
            (emp_list[4], "Improve Engineering Excellence"),
            (emp_list[8], "Boost Customer Satisfaction"),
            (emp_list[9], "Boost Customer Satisfaction"),
            (emp_list[7], "Strengthen Team Culture"),
            (emp_list[6], "Strengthen Team Culture"),
            (emp_list[10], "Boost Customer Satisfaction"),
            (emp_list[12], "Strengthen Team Culture"),
        ]
        for emp, obj_title in assignments:
            obj = objectives[obj_title]
            if EmployeeObjective.objects.filter(
                employee_id=emp, objective_id=obj
            ).exists():
                continue
            eo = EmployeeObjective(
                employee_id=emp,
                objective_id=obj,
                start_date=today - timedelta(days=30),
                end_date=today + timedelta(days=60),
                status=random.choice(
                    ["On Track", "Behind", "Not Started", "At Risk"]
                ),
                progress_percentage=random.randint(10, 80),
            )
            eo.save()

            # Assign key results to employee objective
            for kr in obj.key_result_id.all():
                if not EmployeeKeyResult.objects.filter(
                    employee_objective_id=eo, key_result_id=kr
                ).exists():
                    target = kr.target_value
                    current = random.randint(0, target)
                    ekr = EmployeeKeyResult(
                        employee_objective_id=eo,
                        key_result_id=kr,
                        progress_type=kr.progress_type,
                        target_value=target,
                        start_value=0,
                        current_value=current,
                        start_date=today - timedelta(days=30),
                        end_date=today + timedelta(days=60),
                        status=random.choice(["On Track", "Behind", "Not Started"]),
                        progress_percentage=int((current / target) * 100) if target else 0,
                    )
                    ekr.save()
            eo_count += 1
        self.stdout.write(f"  Assigned {eo_count} employee objectives with key results")

        # Create question template and feedback
        try:
            qt = QuestionTemplate.objects.get(
                question_template="Quarterly Performance Review"
            )
        except QuestionTemplate.DoesNotExist:
            qt = QuestionTemplate(
                question_template="Quarterly Performance Review"
            )
            qt.save()
            qt.company_id.add(company)

            questions = [
                ("How would you rate the employee's overall performance?", "2"),
                ("What are the employee's key strengths?", "1"),
                ("What areas need improvement?", "1"),
                ("Would you recommend this employee for a promotion?", "3"),
            ]
            for q_text, q_type in questions:
                q = Question(question=q_text, question_type=q_type, template_id=qt)
                q.save()
        self.stdout.write("  Created feedback question template")

        # Create feedback cycles
        fb_count = 0
        for i in range(min(5, len(emp_list))):
            emp = emp_list[i]
            if Feedback.objects.filter(
                employee_id=emp, review_cycle="Q2 2026 Review"
            ).exists():
                continue
            fb = Feedback(
                review_cycle="Q2 2026 Review",
                employee_id=emp,
                manager_id=emp.employee_work_info.reporting_manager_id,
                question_template_id=qt,
                start_date=today - timedelta(days=15),
                end_date=today + timedelta(days=45),
                status=random.choice(["On Track", "Not Started"]),
            )
            fb.save()
            # Add colleagues
            colleagues = [e for e in emp_list if e != emp][:3]
            fb.colleague_id.set(colleagues)
            fb_count += 1
        self.stdout.write(f"  Created {fb_count} feedback cycles")

    def _create_asset_data(self, employees, company):
        from asset.models import Asset, AssetAssignment, AssetCategory, AssetLot

        # Create asset categories
        categories_data = [
            "Laptops",
            "Monitors",
            "Mobile Phones",
            "Furniture",
            "Software Licenses",
        ]
        categories = {}
        for name in categories_data:
            try:
                cat = AssetCategory.objects.get(asset_category_name=name)
            except AssetCategory.DoesNotExist:
                cat = AssetCategory(asset_category_name=name)
                cat.save()
                cat.company_id.add(company)
            categories[name] = cat
        self.stdout.write(f"  Created {len(categories)} asset categories")

        # Create asset lot
        try:
            lot = AssetLot.objects.get(lot_number="LOT-2024-001")
        except AssetLot.DoesNotExist:
            lot = AssetLot(
                lot_number="LOT-2024-001",
                lot_description="Q1 2024 IT Equipment Purchase",
            )
            lot.save()
            lot.company_id.add(company)

        # Create assets
        assets_data = [
            ("MacBook Pro 16 M3", "Laptops", "ASSET-LP-001", 220000, "In use"),
            ("MacBook Pro 14 M3", "Laptops", "ASSET-LP-002", 180000, "In use"),
            ("Dell XPS 15", "Laptops", "ASSET-LP-003", 150000, "In use"),
            ("ThinkPad X1 Carbon", "Laptops", "ASSET-LP-004", 140000, "In use"),
            ("MacBook Air M2", "Laptops", "ASSET-LP-005", 120000, "In use"),
            ("Dell Latitude 5540", "Laptops", "ASSET-LP-006", 95000, "Available"),
            ("LG UltraWide 34", "Monitors", "ASSET-MN-001", 45000, "In use"),
            ("Dell U2723QE 27", "Monitors", "ASSET-MN-002", 38000, "In use"),
            ("Samsung 32 4K", "Monitors", "ASSET-MN-003", 35000, "Available"),
            ("iPhone 15 Pro", "Mobile Phones", "ASSET-PH-001", 135000, "In use"),
            ("Samsung Galaxy S24", "Mobile Phones", "ASSET-PH-002", 85000, "In use"),
            ("Standing Desk", "Furniture", "ASSET-FR-001", 25000, "In use"),
            ("Ergonomic Chair", "Furniture", "ASSET-FR-002", 18000, "In use"),
            ("JetBrains All Products", "Software Licenses", "ASSET-SW-001", 30000, "In use"),
            ("Figma Enterprise", "Software Licenses", "ASSET-SW-002", 25000, "In use"),
        ]
        emp_list = list(employees.values())
        assets = {}
        a_count = 0
        for name, cat, tracking, cost, status in assets_data:
            if Asset.objects.filter(asset_tracking_id=tracking).exists():
                assets[tracking] = Asset.objects.get(asset_tracking_id=tracking)
                continue
            asset = Asset(
                asset_name=name,
                asset_category_id=categories[cat],
                asset_tracking_id=tracking,
                asset_purchase_date=date(2024, 1, 15),
                asset_purchase_cost=cost,
                asset_status=status,
                asset_lot_number_id=lot,
            )
            asset.save()
            assets[tracking] = asset
            a_count += 1
        self.stdout.write(f"  Created {a_count} assets")

        # Assign assets to employees
        assign_map = [
            ("ASSET-LP-001", 0),
            ("ASSET-LP-002", 1),
            ("ASSET-LP-003", 2),
            ("ASSET-LP-004", 3),
            ("ASSET-LP-005", 4),
            ("ASSET-MN-001", 0),
            ("ASSET-MN-002", 1),
            ("ASSET-PH-001", 6),
            ("ASSET-PH-002", 8),
            ("ASSET-FR-001", 0),
            ("ASSET-FR-002", 6),
            ("ASSET-SW-001", 0),
            ("ASSET-SW-002", 2),
        ]
        assign_count = 0
        for tracking, emp_idx in assign_map:
            if tracking not in assets:
                continue
            asset = assets[tracking]
            emp = emp_list[emp_idx]
            if AssetAssignment.objects.filter(
                asset_id=asset, return_status__isnull=True
            ).exists():
                continue
            assignment = AssetAssignment(
                asset_id=asset,
                assigned_to_employee_id=emp,
                assigned_by_employee_id=emp_list[12],  # Operations manager
            )
            assignment.save()
            assign_count += 1
        self.stdout.write(f"  Created {assign_count} asset assignments")

    def _create_helpdesk_data(self, employees, company, departments):
        from helpdesk.models import Ticket, TicketType

        # Create ticket types
        ticket_types_data = [
            ("IT Support", "service_request", "ITS"),
            ("HR Query", "service_request", "HRQ"),
            ("Complaint", "complaint", "CMP"),
            ("Suggestion", "suggestion", "SUG"),
        ]
        ticket_types = {}
        for title, typ, prefix in ticket_types_data:
            try:
                tt = TicketType.objects.get(title=title)
            except TicketType.DoesNotExist:
                tt = TicketType(title=title, type=typ, prefix=prefix)
                tt.save()
            ticket_types[title] = tt
        self.stdout.write(f"  Created {len(ticket_types)} ticket types")

        # Create tickets
        emp_list = list(employees.values())
        today = date.today()

        # Map department names to IDs for raised_on field
        from base.models import Department as DeptModel
        dept_id_map = {}
        for d in DeptModel.objects.all():
            dept_id_map[d.department] = str(d.id)

        engineering_id = dept_id_map.get("Engineering", "1")
        hr_id = dept_id_map.get("Human Resources", "1")
        operations_id = dept_id_map.get("Operations", "1")

        tickets_data = [
            {
                "title": "Laptop keyboard not working",
                "employee": emp_list[3],
                "ticket_type": "IT Support",
                "description": "My laptop keyboard has stopped responding after the latest update.",
                "priority": "high",
                "status": "in_progress",
                "raised_on": engineering_id,
                "assigning_type": "department",
            },
            {
                "title": "Leave balance incorrect",
                "employee": emp_list[4],
                "ticket_type": "HR Query",
                "description": "My casual leave balance shows 10 but should be 12 days.",
                "priority": "medium",
                "status": "new",
                "raised_on": hr_id,
                "assigning_type": "department",
            },
            {
                "title": "Office AC not cooling",
                "employee": emp_list[7],
                "ticket_type": "Complaint",
                "description": "The air conditioning in the 3rd floor meeting room is not working properly.",
                "priority": "low",
                "status": "resolved",
                "raised_on": str(emp_list[12].id),
                "assigning_type": "individual",
            },
            {
                "title": "Add standing desks option",
                "employee": emp_list[9],
                "ticket_type": "Suggestion",
                "description": "We should provide standing desk options for employees who prefer them.",
                "priority": "low",
                "status": "new",
                "raised_on": operations_id,
                "assigning_type": "department",
            },
            {
                "title": "VPN access request",
                "employee": emp_list[5],
                "ticket_type": "IT Support",
                "description": "Need VPN access for remote work. Currently unable to connect to internal services.",
                "priority": "high",
                "status": "resolved",
                "raised_on": engineering_id,
                "assigning_type": "department",
            },
            {
                "title": "Salary slip not generated",
                "employee": emp_list[11],
                "ticket_type": "HR Query",
                "description": "March 2026 salary slip is not showing in the payroll section.",
                "priority": "medium",
                "status": "in_progress",
                "raised_on": hr_id,
                "assigning_type": "department",
            },
        ]
        t_count = 0
        for t_data in tickets_data:
            if Ticket.objects.filter(
                title=t_data["title"], employee_id=t_data["employee"]
            ).exists():
                continue
            ticket = Ticket(
                title=t_data["title"],
                employee_id=t_data["employee"],
                ticket_type=ticket_types[t_data["ticket_type"]],
                description=t_data["description"],
                priority=t_data["priority"],
                status=t_data["status"],
                raised_on=t_data["raised_on"],
                assigning_type=t_data["assigning_type"],
            )
            ticket.save()
            # Assign to a manager
            if t_data["status"] != "new":
                ticket.assigned_to.add(emp_list[12])
            t_count += 1
        self.stdout.write(f"  Created {t_count} helpdesk tickets")

    def _create_project_data(self, employees, company):
        from project.models import Project, ProjectStage, Task

        emp_list = list(employees.values())
        today = date.today()

        # Create projects
        projects_data = [
            {
                "title": "HRM Platform Upgrade",
                "description": "Upgrade the HRM platform with new modules including advanced analytics, mobile app integration, and AI-powered insights.",
                "start_date": today - timedelta(days=30),
                "end_date": today + timedelta(days=90),
                "status": "in_progress",
                "managers": [0],
                "members": [1, 2, 3, 4, 5, 14],
            },
            {
                "title": "Q2 Marketing Campaign",
                "description": "Plan and execute Q2 digital marketing campaign across social media and email channels.",
                "start_date": today - timedelta(days=15),
                "end_date": today + timedelta(days=75),
                "status": "in_progress",
                "managers": [8],
                "members": [9],
            },
            {
                "title": "Office Renovation 2026",
                "description": "Renovate the 2nd floor office space with modern collaborative workspaces.",
                "start_date": today + timedelta(days=10),
                "end_date": today + timedelta(days=120),
                "status": "new",
                "managers": [12],
                "members": [13],
            },
        ]

        for p_data in projects_data:
            if Project.objects.filter(title=p_data["title"]).exists():
                continue
            project = Project(
                title=p_data["title"],
                description=p_data["description"],
                start_date=p_data["start_date"],
                end_date=p_data["end_date"],
                status=p_data["status"],
            )
            project.save()
            for idx in p_data["managers"]:
                project.managers.add(emp_list[idx])
            for idx in p_data["members"]:
                project.members.add(emp_list[idx])

            # Add stages (save auto-creates "Todo")
            stages = {}
            for stage_title in ["In Progress", "Review", "Done"]:
                if not ProjectStage.objects.filter(
                    project=project, title=stage_title
                ).exists():
                    stage = ProjectStage(project=project, title=stage_title)
                    stage.save()
                    stages[stage_title] = stage
                else:
                    stages[stage_title] = ProjectStage.objects.get(
                        project=project, title=stage_title
                    )

            todo_stage = ProjectStage.objects.filter(
                project=project, title="Todo"
            ).first()

            # Mark "Done" as end stage
            if "Done" in stages:
                done_stage = stages["Done"]
                done_stage.is_end_stage = True
                done_stage.save()

            # Add tasks for HRM project
            if p_data["title"] == "HRM Platform Upgrade" and todo_stage:
                tasks = [
                    ("Design database schema", "to_do", todo_stage, [1]),
                    ("Build REST API endpoints", "in_progress", stages.get("In Progress", todo_stage), [1, 3]),
                    ("Create frontend components", "in_progress", stages.get("In Progress", todo_stage), [2, 4]),
                    ("Write unit tests", "to_do", todo_stage, [3, 14]),
                    ("Setup CI/CD pipeline", "completed", stages.get("Done", todo_stage), [5]),
                    ("API documentation", "to_do", todo_stage, [1]),
                ]
                for t_title, t_status, t_stage, member_idxs in tasks:
                    if Task.objects.filter(project=project, title=t_title).exists():
                        continue
                    task = Task(
                        title=t_title,
                        project=project,
                        stage=t_stage,
                        status=t_status,
                        description=f"Task: {t_title} for {p_data['title']}",
                        start_date=today - timedelta(days=20),
                        end_date=today + timedelta(days=60),
                    )
                    task.save()
                    task.task_managers.add(emp_list[0])
                    for idx in member_idxs:
                        task.task_members.add(emp_list[idx])

        self.stdout.write(f"  Created {len(projects_data)} projects with stages and tasks")

    def _create_offboarding_data(self, employees, company):
        from offboarding.models import Offboarding, ResignationLetter

        emp_list = list(employees.values())
        today = date.today()

        # Create an offboarding process
        if not Offboarding.objects.filter(title="Standard Exit").exists():
            offboarding = Offboarding(
                title="Standard Exit",
                description="Standard employee offboarding process with exit interview, handover, and FNF settlement.",
                status="ongoing",
            )
            offboarding.save()
            # Add HR manager as offboarding manager
            offboarding.managers.add(emp_list[6])
            self.stdout.write("  Created offboarding process")

        # Create a sample resignation letter
        resigning_emp = emp_list[5]  # Ananya (contract employee)
        if not ResignationLetter.objects.filter(employee_id=resigning_emp).exists():
            resignation = ResignationLetter(
                employee_id=resigning_emp,
                title="Resignation - Contract Completion",
                description="My contract period is ending and I would like to formally resign. Thank you for the opportunity.",
                planned_to_leave_on=today + timedelta(days=30),
                status="requested",
            )
            resignation.save()
            self.stdout.write("  Created sample resignation letter")
