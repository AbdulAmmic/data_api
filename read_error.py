
try:
    with open("check_error.txt", "r", encoding="utf-16") as f:
        print(f.read())
except:
    with open("check_error.txt", "r", encoding="utf-8") as f:
        print(f.read())
