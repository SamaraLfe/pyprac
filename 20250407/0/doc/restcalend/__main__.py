import sys
from . import restmonth


def main():
    if len(sys.argv) != 3:
        print("Usage: python3 -m restcalend <year> <month>")
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

    # Generate reST table and save to file
    table = restmonth(year, month)
    filename = f"calendar_{year}_{month}.rst"
    with open(filename, 'w') as f:
        f.write(table)
    print(f"Generated calendar saved to {filename}")


if __name__ == "__main__":
    main()