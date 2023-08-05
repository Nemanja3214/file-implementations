from app.serial_file import *
from app.sequential_file import *
from app.constants import *
from app.record import *
from datetime import datetime

active_file_sequential = None
rec = Record(DATA_ATTRIBUTES, DATA_FMT, CODING)


def form_new_file(change_file_serial, error_file_sequential, change_file_sequential):
    name = input("Type new file name: ")
    try:
        f = open("data/" + name + ".dat", "x")
        f.close()
    except FileExistsError:
        print("You inputed file name that already exists")


def choose_active_file(change_file_serial, error_file_sequential, change_file_sequential):
    global active_file_sequential
    name = input("Type active file name in data folder(without extension): ")
    try:
        f = open("data/" + name + ".dat", "rb+")
    except FileNotFoundError:
        print("File doesn't exist")
        return None
    active_file_sequential = SequentialFile(f.name, rec, F)
    active_file_sequential.init_file()


def form_change_file_serial(change_file_serial, error_file_sequential, change_file_sequential):
    change_file_serial.init_file()
    change_menu = {
        1: add,
        2: modify,
        3: delete
    }
    while True:
        print("1. Add")
        print("2. Modify")
        print("3. Delete")
        print("4. Back")
        x = input("Input serial number of option: ")
        if x == '4':
            return
        else:
            x = convert_int(x)
            if x is None:
                print("You inputed invalid option, try again")
            elif x in [1, 2, 3]:
                change_menu[x](change_file_serial)
            else:
                print("You inputed invalid option, try again")


def check_date(s):
    try:
        datetime.strptime(s, "%H:%M %d.%m.%Y.")
        return True
    except ValueError:
        return False


def add(change_serial_file):
    data = {}
    id = input("ID: ")
    id = convert_int(id)
    if id is None:
        print("You inputed value that is not int")
        return None
    data["id"] = id

    type_of_animal = input("Type: ")
    data["type"] = type_of_animal

    time_of_shooting = input("Date and time of shooting(HH:mm dd.MM.yyyy.): ")
    if not check_date(time_of_shooting):
        print("Bad time format inputed")
        return None
    data["time of shooting"] = time_of_shooting

    ammo = input("Ammo: ")
    data["ammo used"] = ammo

    weight = input("Weight: ")
    weight = convert_int(weight)
    if weight is None:
        print("You inputed value that is not int")
        return None
    data["weight"] = weight

    data["status"] = 5

    change_serial_file.insert_record_without_check(data)


def modify(change_serial_file):
    data = {}
    id = input("ID: ")
    id = convert_int(id)
    if id is None:
        print("You inputed value that is not int")
        return None
    data["id"] = id

    type_of_animal = input("Type: ")
    data["type"] = type_of_animal

    time_of_shooting = input("Date and time of shooting(HH:mm dd.MM.yyyy.): ")
    data["time of shooting"] = time_of_shooting

    ammo = input("Ammo: ")
    data["ammo used"] = ammo

    weight = input("Weight: ")
    weight = convert_int(weight)
    if weight is None:
        print("You inputed value that is not int")
        return None
    data["weight"] = weight

    data["status"] = 6

    change_serial_file.insert_record_without_check(data)


def delete(change_serial_file):
    data = {}
    id = input("Type syllabus key you want to delete: ")
    id = convert_int(id)
    if id is None:
        print("You inputed value that is not an int")
        return None

    data["id"] = id
    data["type"] = ""
    data["time of shooting"] = ""
    data["ammo used"] = ""
    data["weight"] = 0
    data["status"] = 7

    change_serial_file.insert_record_without_check(data)
    # change_serial_file.print_file()


def form_change_file_sequential(change_file_serial, error_file_sequential, change_file_sequential):
    change_file_sequential.init_file()
    syllable_list = change_file_serial.syllable_list()
    # Timsort stabilno sortiranje
    syllable_list = sorted(syllable_list, key=lambda syllable: syllable["id"])
    for syllable in syllable_list:
        change_file_sequential.insert_record_without_check(syllable)


def show_active_file(change_file_serial, error_file_sequential, change_file_sequential):
    global active_file_sequential
    if active_file_sequential is None:
        print("Active file is has not been initialized")
        return None
    print(active_file_sequential.filename)


def form_out_file(change_file_serial, error_file_sequential, change_file_sequential):
    global active_file_sequential
    if active_file_sequential is None:
        print("Active file has not been chosen")
        return None
    error_file_sequential.init_file()

    index_of_error = 0
    with open(change_file_sequential.filename, "rb") as f:
        while True:
            block = change_file_sequential.read_block(f)

            if not block:
                break

            for syllable in block:
                execute(syllable, index_of_error, error_file_sequential)
                index_of_error += 1


def execute(syllable, index_of_error, error_file_sequential):
    global active_file_sequential
    if active_file_sequential is None:
        print("Active file has not been chosen")
        return None

    if syllable["id"] == -1:
        return

    # adding
    if syllable["status"] == 5:
        syllable["status"] = 1

        if active_file_sequential.find_by_id(syllable.get("id")):
            error_file_sequential.insert_record({"id": index_of_error, "description":
                "Insertion could not be completed because syllable with such key already exists"})

        else:
            active_file_sequential.insert_record_without_check(syllable)

    # modifying
    elif syllable["status"] == 6:
        syllable["status"] = 1

        if not active_file_sequential.find_by_id(syllable.get("id")):
            error_file_sequential.insert_record({"id": index_of_error, "description":
                "Modification could not be completed because syllable with such key doesn't exist"})

        else:
            active_file_sequential.modify(syllable)

    # deletion
    elif syllable["status"] == 7:
        syllable["status"] = 2

        if not active_file_sequential.find_by_id(syllable.get("id")):
            error_file_sequential.insert_record({"id": index_of_error, "description":
                "Insertion could not be completed because syllable with such key doesn't exist"})

        else:
            active_file_sequential.delete_by_id(syllable["id"])


def print_all_active(change_file_serial, error_file_sequential, change_file_sequential):
    global active_file_sequential
    if active_file_sequential is None:
        print("Active file has not been chosen")
        return None
    print("Active file: ")
    active_file_sequential.print_file()


def print_all_error(change_file_serial, error_file_sequential, change_file_sequential):
    print("Error file: ")
    error_file_sequential.print_file()


def convert_int(s):
    try:
        int(s)
        return int(s)
    except ValueError:
        return None


def main():
    menu = {
        1: form_new_file,
        2: choose_active_file,
        3: show_active_file,
        4: form_change_file_serial,
        5: form_change_file_sequential,
        6: form_out_file,
        7: print_all_active,
        8: print_all_error,
        9: lambda x1, x2, x3: exit()

    }
    change_file_serial = SerialFile("data/change_serial.dat", rec, F)
    change_file_serial.init_file()

    error_file_sequential = SequentialFile("data/error.dat", Record(ERR_ATTRIBUTES, ERR_FMT, CODING), F)
    error_file_sequential.init_file()

    change_file_sequential = SequentialFile("data/change_sequential.dat", rec, F)
    change_file_sequential.init_file()

    while True:
        print("Menu")
        print("1. Form new file")
        print("2. Choose active file")
        print("3. Show active file")
        print("4. Form serial change file")
        print("5. Form sequential change file")
        print("6. Form out file")
        print("7. Print all syllables in active file")
        print("8. Print all syllables in error file")
        print("9. Exit")
        x = input("Type option serial number: ")
        x = convert_int(x)
        if x is None:
            print("You inputed invalid option, try again")
        else:
            menu[x](change_file_serial, error_file_sequential, change_file_sequential)


if __name__ == '__main__':
    main()
