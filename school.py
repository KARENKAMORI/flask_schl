# python program that grades entered marks
import re

def main():
    if reg_validator('P15/142480/2021'):
        print("Valid")
    else:
        print("Invalid")
    score = int(input("Score: "))
    print(graded(score))

def graded(score):
    # Best design
    if score >= 70:
        return 'A'
    elif score >= 60:
        return 'B'
    elif score >= 50:
        return 'C'
    elif score >= 40:
        return 'D'
    else:
        return 'F'

def reg_validator(reg_no):
    return re.search("^P15/([0-9]{4}|[0-9]{6})/[0-9]{4}$", reg_no)

if __name__ == "__main__":
    main()