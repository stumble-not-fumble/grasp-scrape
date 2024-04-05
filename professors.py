import glob
import os
import re
from dataclasses import dataclass

import postgrest
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

COURSE_MAPPING = {
    "gender & info tech": "gender and information technology",
    "soc med ethics auto": "social media, ethics, and automation",
    "intro data science": "introduction to data science",
    "exploring inform": "exploring informatics",
    "intell foundations": "intellectual foundations of informatics",
    "data sci foundations": "foundational skills for data science",
    "data rsng digit wrld": "data raising in a digital world",
    "orientation to info": "orientation to informatics",
    "info assr & cybrsec": "information assurance and cybersecurity",
    "entrprise risk mgmt": "enterprise risk management",
    "comp net & dist app": "computer networks and distributed applications",
    "db & data modeling": "database and data modeling",
    "info architecture": "introduction to information architecture",
    "client-side dev": "client-side development",
    "info ethics & policy": "information ethics and policy",
    "race gender & info": "race, gender, and information",
    "indig digital wrld": "indigenous ways of knowing in the digital world",
    "info policy design": "information policy design",
    "moral reason & dsgn": "moral reasoning and interaction design",
    "record of us all": "the record of us all",
    "visual info design": "visual information design",
    "mobile app design": "mobile application design",
    "data science methds": "core methods in data science",
    "adv data sci methds": "advanced methods in data science",
    "is analysis & dsgn": "product and information systems management",
    "professionalism": "professionalism in informatics",
    "topics in cybersec": "emerging topics in information assurance and cybersecurity",
    "db design & mgmt": "database design and management",
    "content strategy": "content strategy in information architecture",
    "server-side dev": "server-side development",
    "coop software dev": "cooperative software development",
    "software arch": "software architecture for interactive systems",
    "android mobile dev": "mobile development: android",
    "ios mobile dev": "mobile development: ios",
    "input & interaction": "input and interaction",
    "val sen design": "value sensitive design",
    "tech time & design": "technology, time and design",
    "des pers hlth & well": "designing for personal health and wellness",
    "interactive info vis": "interactive information visualization",
    "pop health info": "population health informatics",
    "project management": "project management in informatics",
    "capstone project ii": "project capstone ii",
    "internship": "internship in informatics",
    "service lrn in info": "service learning in informatics",
    "topic informatics": "special topics in informatics",
    "ind study": "independent study",
}


@dataclass(frozen=True)
class Course:
    department: str
    number: int
    name: str
    description: str

    def __str__(self):
        return f"{self.department} {self.number} {self.name} {self.description}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Course):
            return NotImplemented
        return (
            self.department == other.department
            and self.number == other.number
            and self.name == other.name
        )

    def __hash__(self) -> int:
        return hash(f"{self.department} {self.number} {self.name}")


@dataclass(frozen=True)
class Professor:
    first_name: str
    last_name: str
    middle_name: str | None
    quarter: str
    year: int
    course: Course

    def __str__(self):
        return f"{self.first_name} {self.middle_name} {self.last_name}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Professor):
            return NotImplemented
        return self.first_name == other.first_name and self.last_name == other.last_name

    def __hash__(self) -> int:
        return hash(f"{self.first_name} {self.last_name}")


professors: list[Professor] = []
for filename in glob.glob(
    "data-timeschd/INFO_*_*.html",
):
    filecoursename, year, quarter = filename.split("_")
    year = int(year)
    quarter = quarter.split(".")[0]
    with open(filename, "r") as file:
        soup = BeautifulSoup(file, "html.parser")

        for row in soup.select("table"):
            if list(row.attrs)[0] == "bgcolor":
                course_tag = row.select_one("tr td[width='50%'] b")
                if course_tag is not None:
                    department, number, name = (
                        course_tag.get_text(separator=" ", strip=True)
                        .replace("\xa0\xa0 ", " ")
                        .split(" ", 2)
                    )
                    current_course = Course(
                        department.strip().lower(),
                        int(number),
                        name.strip().lower(),
                        "",
                    )
                    if current_course.name in COURSE_MAPPING:
                        current_course = Course(
                            current_course.department,
                            current_course.number,
                            COURSE_MAPPING[current_course.name],
                            "",
                        )
            elif list(row.attrs)[0] == "width" and row.select("pre"):
                text_row = row.select_one("pre")
                text = text_row.get_text(separator=" ", strip=True).lower()

                section = re.search(r"[0-9]+ [a-z]  [0-9]", text)
                if section is None:
                    continue

                middle_name_match = re.search(r"  [a-z-.]+,[a-z-.]+ [a-z-.]+  ", text)
                no_middle_name_match = re.search(r"  [a-z-.]+,[a-z-.]+  ", text)
                if middle_name_match:
                    last, first, middle = re.split(
                        r",|\s", middle_name_match[0].strip()
                    )

                    last = last.lower().strip()
                    first = first.lower().strip()
                    middle = middle[0].lower().strip()

                    if len(first) > 1:
                        professors.append(
                            Professor(
                                first, last, middle, quarter, year, current_course
                            )
                        )

                    text.replace(middle_name_match[0], "")
                elif no_middle_name_match:
                    last, first = no_middle_name_match[0].strip().split(",")

                    last = last.lower().strip()
                    first = first.lower().strip()

                    if len(first) > 1:
                        professors.append(
                            Professor(first, last, None, quarter, year, current_course)
                        )

print(f"{len(professors)} professors found.")


CLIENT = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_KEY"],
)

info = CLIENT.storage.from_("scrape").download("info.html")
soup = BeautifulSoup(info, "html.parser")

soup.select_one("p").decompose()

for row in soup.select("p a"):
    row.decompose()

CURRENT_COURSES: set[Course] = set()
for row in soup.select("p"):
    course = row.select_one("b").extract()
    department, number, name = course.get_text(separator=" ", strip=True).split(" ", 2)
    credits = re.search(r"\(.+", name)
    name = name.replace(credits[0], "").strip().lower()
    description = row.get_text(separator=" ", strip=True)
    CURRENT_COURSES.add(
        Course(department.strip().lower(), int(number), name, description)
    )
print(f"{len(CURRENT_COURSES)} courses found.")


db_courses = CLIENT.table("courses").select("id").execute()
if len(db_courses.data) > 0:
    print("Courses already in database.")
else:
    for course in CURRENT_COURSES:
        results = (
            CLIENT.table("courses")
            .insert(
                [
                    {
                        "course_title": course.name,
                        "course_major": course.department,
                        "course_number": course.number,
                        "course_description": course.description,
                    }
                ]
            )
            .execute()
        )
        print(course)
current_professors: list[Professor] = [
    professor for professor in professors if professor.course in CURRENT_COURSES
]
print(f"{len(current_professors)} professors found.")

for professor in current_professors:
    in_course_table = (
        CLIENT.table("courses")
        .select("id")
        .eq("course_title", professor.course.name)
        .execute()
    )
    in_professor_table = (
        CLIENT.table("professors")
        .select("id", "first_name", "last_name")
        .eq("first_name", professor.first_name)
        .eq("last_name", professor.last_name)
        .execute()
    )
    year_id = CLIENT.table("years").select("id").eq("year", professor.year).execute()
    quarter_id = (
        CLIENT.table("quarters").select("id").eq("quarter", professor.quarter).execute()
    )

    if len(in_course_table.data) > 0 and len(in_professor_table.data) > 0:
        try:
            CLIENT.table("courses_professors").insert(
                [
                    {
                        "course_id": in_course_table.data[0]["id"],
                        "professor_id": in_professor_table.data[0]["id"],
                    }
                ]
            ).execute()
            CLIENT.table("courses_times").insert(
                [
                    {
                        "course_id": in_course_table.data[0]["id"],
                        "quarter_id": quarter_id.data[0]["id"],
                        "year_id": year_id.data[0]["id"],
                    }
                ]
            ).execute()
        except postgrest.exceptions.APIError as e:
            if e.json()["code"] != "23505":
                raise e
    elif len(in_course_table.data) > 0 and len(in_professor_table.data) == 0:
        try:
            response = (
                CLIENT.table("professors")
                .insert(
                    [
                        {
                            "first_name": professor.first_name,
                            "last_name": professor.last_name,
                            "middle_initial": professor.middle_name,
                        }
                    ]
                )
                .execute()
            )
            if len(response.data) > 0:
                CLIENT.table("courses_professors").insert(
                    [
                        {
                            "course_id": in_course_table.data[0]["id"],
                            "professor_id": response.data[0]["id"],
                        }
                    ]
                ).execute()
                CLIENT.table("courses_times").insert(
                    [
                        {
                            "course_id": in_course_table.data[0]["id"],
                            "quarter_id": quarter_id.data[0]["id"],
                            "year_id": year_id.data[0]["id"],
                        }
                    ]
                ).execute()
        except postgrest.exceptions.APIError as e:
            if e.json()["code"] != "23505":
                raise e
    elif len(in_course_table.data) == 0 and len(in_professor_table.data) > 0:
        try:
            response = (
                CLIENT.table("courses")
                .insert(
                    [
                        {
                            "course_title": professor.course.name,
                            "course_major": professor.course.department,
                            "course_number": professor.course.number,
                            "course_description": professor.course.description,
                        }
                    ]
                )
                .execute()
            )
            if len(response.data) > 0:
                CLIENT.table("courses_professors").insert(
                    [
                        {
                            "course_id": response.data[0]["id"],
                            "professor_id": in_professor_table.data[0]["id"],
                        }
                    ]
                ).execute()
                CLIENT.table("courses_times").insert(
                    [
                        {
                            "course_id": in_course_table.data[0]["id"],
                            "quarter_id": quarter_id.data[0]["id"],
                            "year_id": year_id.data[0]["id"],
                        }
                    ]
                ).execute()
        except postgrest.exceptions.APIError as e:
            if e.json()["code"] != "23505":
                raise e
