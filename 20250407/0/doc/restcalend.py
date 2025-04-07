import sys
import calendar

if len(sys.argv) != 3:
    print("Usage: python3 restcalend.py <year> <month>")
    sys.exit(1)

try:
    year = int(sys.argv[1])
    month = int(sys.argv[2])
except ValueError:
    print("Year and month must be integers.")
    sys.exit(1)

if month < 1 or month > 12:
    print("Month must be between 1 and 12.")
    sys.exit(1)

month_name = calendar.month_name[month]
table = f".. table:: {month_name} {year}\n\n"
table += "    == == == == == == ==\n"
table += "    Mo Tu We Th Fr Sa Su\n"
table += "    == == == == == == ==\n"

days = calendar.monthrange(year, month)[1]
week = []
for day in range(1, days + 1):
    week.append(f"{day:2}")
    if len(week) == 7 or day == days:
        table += "    " + " ".join(week) + " " * (7 - len(week)) * 2 + "\n"
        week = []
table += "    == == == == == == =="

filename = f"calendar_{year}_{month}.rst"
with open(filename, 'w') as f:
    f.write(table)
print(f"Generated calendar saved to {filename}")