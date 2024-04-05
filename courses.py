import glob
from dataclasses import dataclass

from bs4 import BeautifulSoup


@dataclass(frozen=True)
class Course:
    department: str
    number: str
    name: str

    def __str__(self):
        return f"{self.department} {self.number} {self.name}"


courses_scraped = set()
# courses_scraped = []
for filename in glob.glob("data/INFO_*_*.html"):
    with open(filename, "r") as file:
        soup = BeautifulSoup(file, "html.parser")
        for row in soup.select("table tr td[width='50%'] b"):
            department, number, name = (
                row.get_text(separator=" ", strip=True)
                .replace("\xa0\xa0 ", " ")
                .split(" ", 2)
            )
            courses_scraped.add(Course(department, number, name))

with open("courses.txt", "w") as file:
    for course in courses_scraped:
        file.write(f"{course}\n")
