"""
CSV data loader and database seeder.
Reads sample_people.csv and populates the SQLite database.
"""

import csv
import random
from pathlib import Path
from datetime import date, timedelta

from utils.logger import get_logger

logger = get_logger(__name__)

# ─── Field Definitions ────────────────────────────────────────────────────────

FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael",
    "Linda", "William", "Barbara", "David", "Elizabeth", "Richard", "Susan",
    "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen", "Ahmed",
    "Fatima", "Mohammed", "Aisha", "Ali", "Zara", "Omar", "Layla", "Hassan",
    "Nour", "Wei", "Li", "Ming", "Yan", "Hui", "Jing", "Fang", "Xia",
    "Raj", "Priya", "Amit", "Anjali", "Vikram", "Kavya", "Arjun", "Deepa",
    "Carlos", "Maria", "Luis", "Ana", "Jorge", "Sofia", "Miguel", "Isabella",
    "Emma", "Olivia", "Noah", "Liam", "Ava", "Charlotte", "Lucas", "Amelia",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Wilson",
    "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee",
    "Khan", "Ahmed", "Ali", "Hassan", "Rahman", "Islam", "Sheikh",
    "Chen", "Wang", "Zhang", "Liu", "Yang", "Huang", "Wu", "Zhou",
    "Sharma", "Patel", "Singh", "Kumar", "Gupta", "Verma", "Joshi",
    "Silva", "Santos", "Oliveira", "Costa", "Ferreira", "Alves", "Pereira",
    "O'Brien", "Murphy", "Kelly", "Walsh", "Burke", "Collins", "Campbell",
]

DEPARTMENTS = [
    "Engineering", "Marketing", "Sales", "Human Resources", "Finance",
    "Operations", "Legal", "Research & Development", "Customer Support",
    "Product Management", "Design", "Data Science", "IT", "Procurement",
]

JOB_TITLES = {
    "Engineering": ["Software Engineer", "Senior Engineer", "Lead Developer", "DevOps Engineer", "QA Engineer"],
    "Marketing": ["Marketing Manager", "Content Strategist", "SEO Specialist", "Brand Manager", "Copywriter"],
    "Sales": ["Sales Executive", "Account Manager", "Business Development Rep", "Sales Director", "SDR"],
    "Human Resources": ["HR Manager", "Recruiter", "HR Business Partner", "Compensation Analyst", "L&D Specialist"],
    "Finance": ["Financial Analyst", "Accountant", "CFO", "Auditor", "Budget Analyst"],
    "Operations": ["Operations Manager", "Supply Chain Analyst", "Project Coordinator", "Business Analyst", "COO"],
    "Legal": ["Legal Counsel", "Compliance Officer", "Contract Manager", "Paralegal", "Corporate Lawyer"],
    "Research & Development": ["Research Scientist", "R&D Engineer", "Lab Technician", "Principal Researcher", "Innovation Lead"],
    "Customer Support": ["Support Specialist", "Customer Success Manager", "Support Engineer", "Help Desk Agent", "CX Analyst"],
    "Product Management": ["Product Manager", "Product Owner", "Associate PM", "Director of Product", "Product Analyst"],
    "Design": ["UX Designer", "UI Designer", "Graphic Designer", "Creative Director", "Product Designer"],
    "Data Science": ["Data Scientist", "ML Engineer", "Data Analyst", "BI Developer", "Data Engineer"],
    "IT": ["IT Administrator", "Network Engineer", "Systems Administrator", "IT Manager", "Security Analyst"],
    "Procurement": ["Procurement Manager", "Buyer", "Vendor Relations Manager", "Supply Analyst", "Category Manager"],
}

CITIES = [
    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
    "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose",
    "London", "Manchester", "Birmingham", "Leeds", "Glasgow",
    "Toronto", "Vancouver", "Montreal", "Calgary", "Ottawa",
    "Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide",
    "Dubai", "Abu Dhabi", "Riyadh", "Doha", "Kuwait City",
    "Mumbai", "Delhi", "Bangalore", "Chennai", "Pune",
    "Beijing", "Shanghai", "Guangzhou", "Shenzhen", "Chengdu",
]

COUNTRIES = {
    "New York": "USA", "Los Angeles": "USA", "Chicago": "USA", "Houston": "USA",
    "Phoenix": "USA", "Philadelphia": "USA", "San Antonio": "USA", "San Diego": "USA",
    "Dallas": "USA", "San Jose": "USA",
    "London": "UK", "Manchester": "UK", "Birmingham": "UK", "Leeds": "UK", "Glasgow": "UK",
    "Toronto": "Canada", "Vancouver": "Canada", "Montreal": "Canada", "Calgary": "Canada", "Ottawa": "Canada",
    "Sydney": "Australia", "Melbourne": "Australia", "Brisbane": "Australia", "Perth": "Australia", "Adelaide": "Australia",
    "Dubai": "UAE", "Abu Dhabi": "UAE", "Riyadh": "Saudi Arabia", "Doha": "Qatar", "Kuwait City": "Kuwait",
    "Mumbai": "India", "Delhi": "India", "Bangalore": "India", "Chennai": "India", "Pune": "India",
    "Beijing": "China", "Shanghai": "China", "Guangzhou": "China", "Shenzhen": "China", "Chengdu": "China",
}

SKILLS_POOL = [
    "Python", "JavaScript", "SQL", "Excel", "PowerPoint", "Project Management",
    "Data Analysis", "Machine Learning", "Communication", "Leadership",
    "Java", "C++", "React", "Node.js", "Docker", "Kubernetes", "AWS", "Azure",
    "Tableau", "Power BI", "Negotiation", "Marketing Strategy", "SEO",
    "Figma", "Adobe XD", "Photoshop", "Financial Modeling", "Agile", "Scrum",
]

HOBBIES = [
    "Reading", "Gaming", "Hiking", "Cooking", "Traveling", "Photography",
    "Painting", "Playing guitar", "Cycling", "Swimming", "Yoga", "Running",
    "Chess", "Gardening", "Woodworking", "Knitting", "Dancing", "Podcasting",
]

EDUCATION_LEVELS = ["Bachelor's", "Master's", "PhD", "Associate's", "Diploma", "High School"]
EDUCATION_FIELDS = [
    "Computer Science", "Business Administration", "Engineering", "Mathematics",
    "Marketing", "Finance", "Psychology", "Economics", "Physics", "Chemistry",
]


def _random_date(start_year: int, end_year: int) -> str:
    """Generate a random date string between two years."""
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    delta = (end - start).days
    return (start + timedelta(days=random.randint(0, delta))).isoformat()


def _random_phone() -> str:
    """Generate a plausible random phone number."""
    area = random.randint(200, 999)
    mid = random.randint(200, 999)
    end = random.randint(1000, 9999)
    return f"+1-{area}-{mid}-{end}"


def _random_email(first: str, last: str, idx: int) -> str:
    """Generate a unique email from first/last name."""
    domains = ["gmail.com", "outlook.com", "yahoo.com", "company.org", "work.io"]
    domain = random.choice(domains)
    return f"{first.lower()}.{last.lower()}{idx}@{domain}"


def generate_dummy_data(count: int = 1000) -> list[dict]:
    """
    Generate a list of dummy person records.

    Args:
        count: Number of records to generate (default 1000).

    Returns:
        List of dicts with person data.
    """
    records = []
    random.seed(42)  # reproducible data

    for i in range(1, count + 1):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        department = random.choice(DEPARTMENTS)
        city = random.choice(CITIES)
        skills = random.sample(SKILLS_POOL, k=random.randint(3, 7))
        hobbies = random.sample(HOBBIES, k=random.randint(2, 4))
        edu_level = random.choice(EDUCATION_LEVELS)
        edu_field = random.choice(EDUCATION_FIELDS)

        records.append({
            "id": i,
            "first_name": first,
            "last_name": last,
            "full_name": f"{first} {last}",
            "email": _random_email(first, last, i),
            "phone": _random_phone(),
            "date_of_birth": _random_date(1965, 2000),
            "city": city,
            "country": COUNTRIES.get(city, "Unknown"),
            "department": department,
            "job_title": random.choice(JOB_TITLES[department]),
            "salary": random.randint(35_000, 200_000),
            "hire_date": _random_date(2005, 2024),
            "education_level": edu_level,
            "education_field": edu_field,
            "skills": ", ".join(skills),
            "hobbies": ", ".join(hobbies),
            "linkedin": f"https://linkedin.com/in/{first.lower()}-{last.lower()}-{i}",
            "notes": f"Experienced professional with background in {edu_field}.",
        })

    return records


def generate_csv(output_path: str | Path = None, count: int = 1000) -> Path:
    """
    Generate dummy people data and write it to a CSV file.

    Args:
        output_path: Destination path for the CSV. Defaults to data/sample_people.csv.
        count: Number of records to generate.

    Returns:
        Path to the generated CSV file.
    """
    if output_path is None:
        output_path = Path(__file__).resolve().parent.parent / "data" / "sample_people.csv"

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    records = generate_dummy_data(count)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)

    logger.info(f"[green]✓[/green] Generated {count} records → {output_path}")
    return output_path


if __name__ == "__main__":
    generate_csv()
