"""
Create dummy data for all modules in Horilla HRM.
Run with: python manage.py shell < create_dummy_data.py
"""
from datetime import date, time, timedelta
from decimal import Decimal
from django.contrib.auth.models import User
from django.db import IntegrityError

def get_or_make(model, lookup, defaults=None):
    """Helper: get or create without triggering save(**kwargs) issues."""
    try:
        return model.objects.get(**lookup), False
    except model.DoesNotExist:
        params = {**lookup, **(defaults or {})}
        obj = model(**params)
        obj.save()
        return obj, True

# ── Base ────────────────────────────────────────────────────────
from base.models import Company, Department, JobPosition, JobRole, WorkType, EmployeeShift

company, _ = get_or_make(Company, {"company": "Synergific Software"}, {"address": "123 Tech Park", "country": "India", "state": "Karnataka", "city": "Bangalore", "zip": "560001"})
company2, _ = get_or_make(Company, {"company": "Nova Digital"}, {"address": "456 Innovation Hub", "country": "India", "state": "Maharashtra", "city": "Mumbai", "zip": "400001"})

depts = {}
for name in ["Engineering", "Human Resources", "Finance", "Marketing", "Operations"]:
    d, _ = get_or_make(Department, {"department": name})
    d.company_id.add(company)
    depts[name] = d

positions = {}
pos_data = {
    "Software Engineer": "Engineering",
    "Senior Developer": "Engineering",
    "HR Manager": "Human Resources",
    "HR Executive": "Human Resources",
    "Accountant": "Finance",
    "Finance Manager": "Finance",
    "Marketing Lead": "Marketing",
    "Operations Manager": "Operations",
}
for title, dept_name in pos_data.items():
    p, _ = get_or_make(JobPosition, {"job_position": title, "department_id": depts[dept_name]})
    p.company_id.add(company)
    positions[title] = p

roles = {}
role_data = {
    "Backend Developer": "Software Engineer",
    "Frontend Developer": "Software Engineer",
    "Tech Lead": "Senior Developer",
    "Recruiter": "HR Executive",
    "Payroll Officer": "HR Manager",
    "Tax Analyst": "Accountant",
}
for role_name, pos_name in role_data.items():
    r, _ = get_or_make(JobRole, {"job_role": role_name, "job_position_id": positions[pos_name]})
    r.company_id.add(company)
    roles[role_name] = r

work_types = {}
for wt in ["Full Time", "Part Time", "Remote", "Hybrid"]:
    w, _ = get_or_make(WorkType, {"work_type": wt})
    w.company_id.add(company)
    work_types[wt] = w

shifts = {}
for shift_name, full_time in [("Morning", "08:00"), ("General", "09:00"), ("Night", "08:00")]:
    s, _ = get_or_make(EmployeeShift, {"employee_shift": shift_name}, {"full_time": full_time})
    s.company_id.add(company)
    shifts[shift_name] = s

print("[OK] Base data created.")

# ── Employees ───────────────────────────────────────────────────
from employee.models import Employee, EmployeeBankDetails, EmployeeWorkInformation

employees_data = [
    {"first": "Rahul", "last": "Sharma", "email": "rahul.sharma@synergific.com", "phone": "9876543210", "gender": "male", "pos": "Software Engineer", "role": "Backend Developer", "dept": "Engineering", "salary": 85000},
    {"first": "Priya", "last": "Patel", "email": "priya.patel@synergific.com", "phone": "9876543211", "gender": "female", "pos": "Senior Developer", "role": "Tech Lead", "dept": "Engineering", "salary": 120000},
    {"first": "Amit", "last": "Kumar", "email": "amit.kumar@synergific.com", "phone": "9876543212", "gender": "male", "pos": "HR Manager", "role": "Payroll Officer", "dept": "Human Resources", "salary": 95000},
    {"first": "Sneha", "last": "Reddy", "email": "sneha.reddy@synergific.com", "phone": "9876543213", "gender": "female", "pos": "HR Executive", "role": "Recruiter", "dept": "Human Resources", "salary": 55000},
    {"first": "Vikram", "last": "Singh", "email": "vikram.singh@synergific.com", "phone": "9876543214", "gender": "male", "pos": "Accountant", "role": "Tax Analyst", "dept": "Finance", "salary": 70000},
    {"first": "Ananya", "last": "Gupta", "email": "ananya.gupta@synergific.com", "phone": "9876543215", "gender": "female", "pos": "Marketing Lead", "role": None, "dept": "Marketing", "salary": 90000},
    {"first": "Rajesh", "last": "Nair", "email": "rajesh.nair@synergific.com", "phone": "9876543216", "gender": "male", "pos": "Operations Manager", "role": None, "dept": "Operations", "salary": 100000},
    {"first": "Deepika", "last": "Joshi", "email": "deepika.joshi@synergific.com", "phone": "9876543217", "gender": "female", "pos": "Software Engineer", "role": "Frontend Developer", "dept": "Engineering", "salary": 80000},
    {"first": "Karthik", "last": "Menon", "email": "karthik.menon@synergific.com", "phone": "9876543218", "gender": "male", "pos": "Finance Manager", "role": None, "dept": "Finance", "salary": 110000},
    {"first": "Meera", "last": "Das", "email": "meera.das@synergific.com", "phone": "9876543219", "gender": "female", "pos": "Software Engineer", "role": "Backend Developer", "dept": "Engineering", "salary": 75000},
]

employees = []
for i, ed in enumerate(employees_data):
    username = ed["email"].split("@")[0]
    user, created = User.objects.get_or_create(
        username=username,
        defaults={"email": ed["email"], "first_name": ed["first"], "last_name": ed["last"]},
    )
    if created:
        user.set_password("Test@1234")
        user.save()

    emp, _ = get_or_make(Employee, {"employee_user_id": user}, {
        "employee_first_name": ed["first"],
        "employee_last_name": ed["last"],
        "email": ed["email"],
        "phone": ed["phone"],
        "gender": ed["gender"],
        "is_active": True,
    })
    employees.append(emp)

    # Work info
    try:
        wi = EmployeeWorkInformation.objects.get(employee_id=emp)
    except EmployeeWorkInformation.DoesNotExist:
        wi = EmployeeWorkInformation(employee_id=emp)
    wi.department_id = depts[ed["dept"]]
    wi.job_position_id = positions[ed["pos"]]
    wi.job_role_id = roles.get(ed["role"])
    wi.company_id = company
    wi.shift_id = shifts["General"]
    wi.work_type_id = work_types["Full Time"]
    wi.date_joining = date.today() - timedelta(days=365 + i * 30)
    wi.basic_salary = ed["salary"]
    wi.salary_hour = round(ed["salary"] / 176, 2)
    wi.save()

    # Bank details
    try:
        bd = EmployeeBankDetails.objects.get(employee_id=emp)
    except EmployeeBankDetails.DoesNotExist:
        bd = EmployeeBankDetails(employee_id=emp)
    bd.bank_name = ["HDFC Bank", "ICICI Bank", "SBI", "Axis Bank", "Kotak"][i % 5]
    bd.account_number = f"10020030{40 + i:02d}"
    bd.branch = "Main Branch"
    bd.country = "India"
    bd.state = "Karnataka"
    bd.city = "Bangalore"
    bd.save()

print(f"[OK] {len(employees)} employees created.")

# ── Contracts ───────────────────────────────────────────────────
from payroll.models.models import Contract

for i, emp in enumerate(employees):
    try:
        Contract.objects.get(employee_id=emp, contract_name=f"Contract-{emp.employee_first_name}-2024")
    except Contract.DoesNotExist:
        c = Contract(
            employee_id=emp,
            contract_name=f"Contract-{emp.employee_first_name}-2024",
            contract_start_date=date.today() - timedelta(days=365),
            contract_end_date=date.today() + timedelta(days=365),
            wage=employees_data[i]["salary"],
            wage_type="monthly",
            contract_status="active",
        )
        c.save()

print("[OK] Contracts created.")

# ── Allowances & Deductions ─────────────────────────────────────
from payroll.models.models import Allowance, Deduction

# Use bulk_create / update_or_create at DB level to bypass custom save() needing request
from django.db import connection

for title, is_fixed, amount, based_on, rate in [
    ("House Rent Allowance", True, 5000, "basic_pay", 0),
    ("Transport Allowance", True, 2000, "basic_pay", 0),
    ("Medical Allowance", True, 1500, "basic_pay", 0),
    ("Performance Bonus", False, 0, "basic_pay", 10),
]:
    if not Allowance.objects.filter(title=title).exists():
        Allowance.objects.bulk_create([Allowance(title=title, is_fixed=is_fixed, amount=amount, based_on=based_on, rate=rate, include_active_employees=True)])

for title, is_fixed, amount, based_on, rate, is_tax, is_pretax in [
    ("Provident Fund", False, 0, "basic_pay", 12, False, True),
    ("Professional Tax", True, 200, "basic_pay", 0, False, False),
    ("Income Tax", False, 0, "basic_pay", 5, True, True),
]:
    if not Deduction.objects.filter(title=title).exists():
        Deduction.objects.bulk_create([Deduction(title=title, is_fixed=is_fixed, amount=amount, based_on=based_on, rate=rate, is_tax=is_tax, is_pretax=is_pretax, include_active_employees=True)])

print("[OK] Allowances & Deductions created.")

# ── Payslips ────────────────────────────────────────────────────
from payroll.models.models import Payslip

statuses = ["draft", "review_ongoing", "confirmed", "paid"]
for i, emp in enumerate(employees):
    for month_offset in [2, 1]:
        start = (date.today().replace(day=1) - timedelta(days=30 * month_offset)).replace(day=1)
        end = (start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        salary = employees_data[i]["salary"]
        gross = salary + 8500
        deduction = round(salary * 0.17, 2)
        net = round(gross - deduction, 2)

        if not Payslip.objects.filter(employee_id=emp, start_date=start, end_date=end).exists():
            ps = Payslip(
                employee_id=emp, start_date=start, end_date=end,
                group_name=f"Batch-{start.strftime('%b-%Y')}",
                contract_wage=salary, basic_pay=salary, gross_pay=gross,
                deduction=deduction, net_pay=net, status=statuses[i % 4],
                pay_head_data={"basic_pay": {"amount": salary}, "gross_pay": {"amount": gross}, "net_pay": {"amount": net}},
            )
            ps.save()

print("[OK] Payslips created.")

# ── Leave ───────────────────────────────────────────────────────
try:
    from leave.models import LeaveType, AvailableLeave, LeaveRequest

    leave_types = []
    for name, payment, total in [("Casual Leave", "paid", 12), ("Sick Leave", "paid", 10), ("Earned Leave", "paid", 15), ("Loss of Pay", "unpaid", 365)]:
        if not LeaveType.objects.filter(name=name).exists():
            LeaveType.objects.bulk_create([LeaveType(name=name, payment=payment, total_days=total, company_id=company)])
        leave_types.append(LeaveType.objects.get(name=name))

    for emp in employees:
        for lt in leave_types:
            if not AvailableLeave.objects.filter(employee_id=emp, leave_type_id=lt).exists():
                AvailableLeave.objects.bulk_create([AvailableLeave(employee_id=emp, leave_type_id=lt, available_days=lt.total_days, assigned_date=date.today())])

    for i, emp in enumerate(employees[:5]):
        sd = date.today() + timedelta(days=10 + i * 3)
        if not LeaveRequest.objects.filter(employee_id=emp, start_date=sd).exists():
            LeaveRequest.objects.bulk_create([LeaveRequest(
                employee_id=emp, leave_type_id=leave_types[i % 3],
                start_date=sd, end_date=sd + timedelta(days=1),
                description=f"Personal work - {emp.employee_first_name}",
                status=["requested", "approved", "requested", "approved", "requested"][i],
            )])

    print("[OK] Leave data created.")
except Exception as e:
    print(f"[WARN] Leave: {e}")

# ── Attendance ──────────────────────────────────────────────────
try:
    from attendance.models import Attendance

    for emp in employees:
        for day_offset in range(1, 8):
            att_date = date.today() - timedelta(days=day_offset)
            if att_date.weekday() >= 5:
                continue
            if not Attendance.objects.filter(employee_id=emp, attendance_date=att_date).exists():
                att = Attendance(
                    employee_id=emp, attendance_date=att_date,
                    shift_id=shifts["General"], work_type_id=work_types["Full Time"],
                    attendance_clock_in_date=att_date, attendance_clock_in=time(9, 0),
                    attendance_clock_out_date=att_date, attendance_clock_out=time(18, 0),
                    attendance_worked_hour="09:00", minimum_hour="08:00",
                    attendance_validated=True,
                )
                att.save()

    print("[OK] Attendance created.")
except Exception as e:
    print(f"[WARN] Attendance: {e}")

# ── Assets ──────────────────────────────────────────────────────
try:
    from asset.models import AssetCategory, Asset, AssetAssignment

    categories = {}
    for cat_name in ["Laptops", "Monitors", "Mobile Phones", "Chairs", "ID Cards"]:
        c, _ = get_or_make(AssetCategory, {"asset_category_name": cat_name}, {"asset_category_description": f"Company {cat_name.lower()}"})
        c.company_id.add(company)
        categories[cat_name] = c

    assets = []
    for idx, (name, cat, cost) in enumerate([
        ("Dell Latitude 5540", "Laptops", 85000), ("MacBook Pro 14", "Laptops", 175000),
        ("Dell UltraSharp 27", "Monitors", 32000), ("LG 24 IPS", "Monitors", 18000),
        ("iPhone 15", "Mobile Phones", 79900), ("Samsung Galaxy S24", "Mobile Phones", 74999),
        ("Herman Miller Aeron", "Chairs", 95000), ("Steelcase Leap", "Chairs", 65000),
        ("ThinkPad X1 Carbon", "Laptops", 145000), ("Dell P2723QE", "Monitors", 42000),
    ]):
        tracking = f"AST-2024{idx+1:03d}"
        a, _ = get_or_make(Asset, {"asset_tracking_id": tracking}, {
            "asset_name": name, "asset_category_id": categories[cat],
            "asset_purchase_date": date.today() - timedelta(days=180 + idx * 15),
            "asset_purchase_cost": Decimal(str(cost)),
            "asset_status": "In use" if idx < 7 else "Available",
        })
        assets.append(a)

    for i in range(min(7, len(assets), len(employees))):
        if not AssetAssignment.objects.filter(asset_id=assets[i], assigned_to_employee_id=employees[i]).exists():
            aa = AssetAssignment(asset_id=assets[i], assigned_to_employee_id=employees[i], assigned_by_employee_id=employees[0])
            aa.save()

    print("[OK] Assets created.")
except Exception as e:
    print(f"[WARN] Assets: {e}")

# ── Recruitment ─────────────────────────────────────────────────
try:
    from recruitment.models import Recruitment, Candidate, Stage

    recruitments = []
    for title, pos_name, vacancy in [
        ("Python Developer Hiring", "Software Engineer", 3),
        ("HR Analyst Hiring", "HR Executive", 2),
        ("Senior Finance Role", "Finance Manager", 1),
    ]:
        rec, _ = get_or_make(Recruitment, {"title": title}, {
            "company_id": company, "job_position_id": positions[pos_name],
            "vacancy": vacancy, "is_published": True, "start_date": date.today() - timedelta(days=30),
        })
        rec.recruitment_managers.add(employees[2])
        recruitments.append(rec)

    stage_types = ["initial", "test", "interview", "hired"]
    stage_names = ["Application Review", "Technical Test", "Interview", "Offer"]
    all_stages = {}
    for rec in recruitments:
        stages = []
        for idx, (stype, sname) in enumerate(zip(stage_types, stage_names)):
            stg, _ = get_or_make(Stage, {"recruitment_id": rec, "stage": sname}, {"stage_type": stype, "sequence": idx + 1})
            stg.stage_managers.add(employees[2])
            stages.append(stg)
        all_stages[rec.title] = stages

    candidates_data = [
        ("Arjun Verma", "arjun.v@gmail.com", "9000000001"),
        ("Neha Kapoor", "neha.k@gmail.com", "9000000002"),
        ("Rohan Mehta", "rohan.m@gmail.com", "9000000003"),
        ("Kavita Rao", "kavita.r@gmail.com", "9000000004"),
        ("Suresh Iyer", "suresh.i@gmail.com", "9000000005"),
        ("Pallavi Jain", "pallavi.j@gmail.com", "9000000006"),
    ]
    for i, (name, email, mobile) in enumerate(candidates_data):
        rec = recruitments[i % len(recruitments)]
        stages = all_stages[rec.title]
        try:
            Candidate.objects.get(email=email, recruitment_id=rec)
        except Candidate.DoesNotExist:
            c = Candidate(name=name, email=email, mobile=mobile, recruitment_id=rec,
                          stage_id=stages[i % len(stages)], job_position_id=rec.job_position_id)
            c.save()

    print("[OK] Recruitment data created.")
except Exception as e:
    print(f"[WARN] Recruitment: {e}")

# ── Loans ───────────────────────────────────────────────────────
try:
    from payroll.models.models import LoanAccount

    for emp, title, amount, installments, loan_type in [
        (employees[0], "Home Advance", 100000, 10, "loan"),
        (employees[3], "Personal Loan", 50000, 5, "loan"),
        (employees[7], "Salary Advance", 25000, 3, "advanced_salary"),
    ]:
        if not LoanAccount.objects.filter(employee_id=emp, title=title).exists():
            LoanAccount.objects.bulk_create([LoanAccount(
                employee_id=emp, title=title, loan_amount=amount,
                installments=installments, installment_amount=amount / installments,
                provided_date=date.today() - timedelta(days=60),
                installment_start_date=date.today() - timedelta(days=30),
                type=loan_type,
            )])

    print("[OK] Loans created.")
except Exception as e:
    print(f"[WARN] Loans: {e}")

# ── Salary Disbursement ────────────────────────────────────────
from payroll.models.models import SalaryDisbursementSchedule

if not SalaryDisbursementSchedule.objects.filter(company_id=company).exists():
    s = SalaryDisbursementSchedule(company_id=company, disburse_day="last day", auto_disburse=True)
    s.save()
if not SalaryDisbursementSchedule.objects.filter(company_id=company2).exists():
    s = SalaryDisbursementSchedule(company_id=company2, disburse_day="25", auto_disburse=False)
    s.save()

print("[OK] Salary Disbursement schedules created.")

# ── Onboarding ──────────────────────────────────────────────────
try:
    from onboarding.models import OnboardingStage, OnboardingTask, OnboardingPortal

    if recruitments:
        ob_stages = []
        for stitle, seq in [("Document Collection", 1), ("IT Setup", 2), ("Orientation", 3)]:
            obs, _ = get_or_make(OnboardingStage, {"stage_title": stitle, "recruitment_id": recruitments[0]}, {"sequence": seq})
            obs.employee_id.add(employees[2])
            ob_stages.append(obs)

        for ttitle, stage in [
            ("Submit ID proof", ob_stages[0]), ("Submit address proof", ob_stages[0]),
            ("Laptop assignment", ob_stages[1]), ("Email account setup", ob_stages[1]),
            ("Company policy walkthrough", ob_stages[2]), ("Team introduction", ob_stages[2]),
        ]:
            obt, _ = get_or_make(OnboardingTask, {"task_title": ttitle, "stage_id": stage})
            obt.employee_id.add(employees[2])

    print("[OK] Onboarding data created.")
except Exception as e:
    print(f"[WARN] Onboarding: {e}")

# ── PMS ─────────────────────────────────────────────────────────
try:
    from pms.models import Period, Objective, KeyResult, EmployeeObjective

    period, _ = get_or_make(Period, {"period_name": "Q2 2026"}, {"start_date": date(2026, 4, 1), "end_date": date(2026, 6, 30)})
    period.company_id.add(company)

    key_results = []
    for kr_title, kr_desc in [("Code Quality", "Maintain code coverage above 80%"), ("Customer Satisfaction", "Achieve NPS score of 70+"), ("Revenue Growth", "Increase monthly revenue by 15%")]:
        if not KeyResult.objects.filter(title=kr_title).exists():
            KeyResult.objects.bulk_create([KeyResult(title=kr_title, description=kr_desc, company_id=company)])
        key_results.append(KeyResult.objects.get(title=kr_title))

    objectives = []
    for obj_title, obj_desc in [("Improve Product Quality", "Reduce production bugs by 50%"), ("Team Development", "Complete skill matrix for all team members"), ("Process Optimization", "Automate 3 manual processes")]:
        if not Objective.objects.filter(title=obj_title).exists():
            Objective.objects.bulk_create([Objective(title=obj_title, description=obj_desc, company_id=company)])
        objectives.append(Objective.objects.get(title=obj_title))

    pms_statuses = ["Not Started", "On Track", "Behind", "On Track", "At Risk"]
    for i, emp in enumerate(employees[:5]):
        if not EmployeeObjective.objects.filter(employee_id=emp, objective_id=objectives[i % len(objectives)]).exists():
            EmployeeObjective.objects.bulk_create([EmployeeObjective(
                employee_id=emp, objective_id=objectives[i % len(objectives)],
                start_date=date(2026, 4, 1), end_date=date(2026, 6, 30),
                status=pms_statuses[i], progress_percentage=[0, 45, 20, 60, 15][i],
            )])

    print("[OK] PMS data created.")
except Exception as e:
    print(f"[WARN] PMS: {e}")

print("\n=== ALL DUMMY DATA CREATED SUCCESSFULLY ===")
