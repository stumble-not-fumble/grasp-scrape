import requests
from bs4 import BeautifulSoup

QUARTERS = ["AUT", "WIN", "SPR", "SUM"]
YEARS = range(2003, 2025)

for year in YEARS:
    for quarter in QUARTERS:
        url = f"https://www.washington.edu/students/timeschd/{quarter}{year}/info.html"
        response = requests.get(url)
        if response.status_code == 200:
            print(f"Success: {url}")
            with open(f"data/INFO_{year}_{quarter}.html", "wb") as file:
                soup = BeautifulSoup(response.content, "html.parser")
                file.write(soup.prettify("utf-8"))
        else:
            print(f"Failure: {url} ({response.status_code})")
