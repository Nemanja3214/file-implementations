#!/usr/bin/python

from app.constants import *
from app.record import Record
from app.linked_hash_file import LinkedHashFile
import struct
from datetime import datetime
import csv
rec = Record(ATTRIBUTES, FMT, CODING)


def read_txt(fn):
    rows = []
    with open(fn, "r") as f:
        for line in f.readlines():
            cols = line.split()
            rows.append({
                "id": int(cols[0]),
                "name": cols[1],
                "q": float(cols[2]),
                "status": 1
            })
    return rows


def form_new_file():
    name = input("Type new file name: ")
    try:
        f = open("data/" + name + ".dat", "x")
        f.close()
        hash_file = LinkedHashFile(f.name, rec, F, B, struct.calcsize(BLOCK_HEADER_FMT))
        hash_file.init_file()
    except FileExistsError:
        print("You inputed file name that already exists")


def choose_active_file(active_file):
    if active_file is not None:
        active_file.save_E()

    name = input("Type active file name in data folder(without extension): ")
    try:
        f = open("data/" + name + ".dat", "rb+")
    except FileNotFoundError:
        print("File doesn't exist")
        return None
    active_file = LinkedHashFile(f.name, rec, F, B, struct.calcsize(BLOCK_HEADER_FMT))
    active_file.load_E()
    return active_file


def convert_int(s):
    try:
        int(s)
        return int(s)
    except ValueError:
        return None


def show_active_file(active_file):
    if active_file is None:
        print("Active file is has not been initialized")
        return None
    print(active_file.filename)


def check_date(s):
    try:
        datetime.strptime(s, "%H:%M %d.%m.%Y.")
        return True
    except ValueError:
        return False


def insert_new_record(active_file):
    if active_file is None:
        print("Active file has not been initialized")
        return None
    data = {}
    id = input("Input id: ")
    id = convert_int(id)
    if id is None:
        print("You inputed value that is not int")
        return None
    data["id"] = id

    account_number = input("Input account number")
    data["account number"] = account_number

    date = input("Input date and time of transaction")
    # uslov
    if not check_date(date):
        print("Bad time format inputed")
        return None
    data["date"] = date

    description = input("Input description of transaction")
    data["description of purpouse"] = description

    ammount = input("Input ammount of money included in transaction")
    ammount = convert_int(ammount)
    if ammount is None:
        print("You inputed value that is not int")
        return None
    data["ammount"] = ammount

    data["status"] = 1
    data["next block id"] = -1
    data["next syllable id"] = -1
    active_file.insert_record(data)


def search_record(active_file):
    if active_file is None:
        print("Active file has not been initialized")
        return None
    x = input("Input id of record")
    x = convert_int(x)
    if x is None:
        print("You inputed value that is not int")
        return None
    found = active_file.find_by_id(x)
    if found is None:
        print("No record with such id exists")
        return None
    else:
        print("Block id = {0}, record id = {1}".format(found[0], found[1]))


def print_all(active_file):
    if active_file is None:
        print("Active file has not been initialized")
        return None
    active_file.print_file()


def delete_record(active_file):
    if active_file is None:
        print("Active file has not been initialized")
        return None
    x = input("Input id of record you want to delete: ")
    x = convert_int(x)
    if x is None:
        print("You inputed value that is not int")
        return None
    active_file.delete_by_id(x)


def write_tests():
    with open('data/in.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=';',
                            quotechar='|', quoting=csv.QUOTE_NONNUMERIC)
        values = [10, "12345", "12:12 5.5.2021.", "uplata", 10000, 1, -1, -1]

        for i in range(11):
            values[0] += B
            writer.writerow(values)

        values[0] = 9
        writer.writerow(values)

        values[0] = 18
        writer.writerow(values)


def load_tests():
    attributes = ["id", "account number", "date", "description of purpouse", "ammount", "status", "next block id",
                  "next syllable id"]
    fn = "data/test.dat"
    test_file = LinkedHashFile(fn, rec, F, B, struct.calcsize(BLOCK_HEADER_FMT))
    test_file.init_file()
    with open('data/in.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile, fieldnames=attributes, delimiter=';',
                                quotechar='|', quoting=csv.QUOTE_NONNUMERIC)
        for row in reader:
            for key in row:
                if isinstance(row[key], float):
                    row[key] = int(row[key])
            test_file.insert_record(row)


def close(active_file):
    if active_file is not None:
        active_file.save_E()
    exit(0)


def main():
    active_file = None

    while True:
        print("Menu")
        print("1. Form new file")
        print("2. Choose active file")
        print("3. Show active file")
        print("4. Insert new record")
        print("5. Search record")
        print("6. Print all")
        print("7. Delete record")
        print("8. Prepare in file")
        print("9. Prepare test")
        print("10. Exit")
        x = input("Type option serial number: ")
        x = convert_int(x)
        if x is None:
            print("You inputed invalid option, try again")
        elif 0 > x > 10:
            print("You inputed invalid option, try again")
        else:
            if x == 1:
                form_new_file()
            elif x == 2:
                active_file = choose_active_file(active_file)
            elif x == 3:
                show_active_file(active_file)
            elif x == 4:
                insert_new_record(active_file)
            elif x == 5:
                search_record(active_file)
            elif x == 6:
                print_all(active_file)
            elif x == 7:
                delete_record(active_file)
            elif x == 8:
                write_tests()
            elif x == 9:
                load_tests()
            elif x == 10:
                close(active_file)
            else:
                print("You inputed invalid option, try again")


if __name__ == "__main__":
    main()
