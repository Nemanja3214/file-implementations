#!/usr/bin/python

import os
import struct

from app.binary_file import BinaryFile
from app.block import *
from app.constants import *
from app.record import *


class LinkedHashFile(BinaryFile):
    def __init__(self, filename, record, blocking_factor, b, block_header_size, empty_key=-1):
        BinaryFile.__init__(self, filename, record, blocking_factor, block_header_size, empty_key)
        self.b = b
        self.E = 0
        self.E_location = self.block_size * b

    def save_E(self):
        with open(self.filename, "rb+") as f:
            f.seek(0, 2)
            f.write(struct.pack("i", self.E))

    def load_E(self):
        with open(self.filename, "rb+") as f:
            size = struct.calcsize("i")
            f.seek(-size, 2)
            self.E = struct.unpack("i", f.read(size))[0]

    def hash(self, id):
        return id % self.b

    def write_block(self, file, block):
        binary_data = bytearray()

        header_binary_data = block.header_to_encoded_values()
        binary_data.extend(header_binary_data)

        for rec in block.data:
            rec_binary_data = self.record.dict_to_encoded_values(rec)
            binary_data.extend(rec_binary_data)

        file.write(binary_data)

    def read_block(self, file):
        binary_data = file.read(self.block_size)
        block = Block(self.blocking_factor)

        if len(binary_data) == 0:
            return block

        t = struct.unpack(BLOCK_HEADER_FMT, binary_data[0: self.block_header_size])
        t = [t[i].decode(CODING).strip('\x00') if isinstance(t[i], bytes) else t[i] for i in range(len(t))]
        block.u_block = t[0]
        block.u_syllable = t[1]
        block.b = t[2]
        block.n = t[3]
        block.e = t[4]

        for i in range(self.blocking_factor):  # slajsingom izdvajamo niz bita za svaki slog, i potom vrsimo otpakivanje
            begin = self.block_header_size + self.record_size * i
            end = self.block_header_size + self.record_size * (i + 1)
            block.data.append(self.record.encoded_tuple_to_dict(
                binary_data[begin:end]))

        return block

    def get_empty_rec(self):
        syllable = {"id": self.empty_key}
        i = 1
        for c in self.record.format[1:]:
            if not c.isalpha():
                continue
            if c == 's':
                syllable[self.record.attributes[i]] = ""
                i += 1
            else:
                syllable[self.record.attributes[i]] = -1
                i += 1
        return syllable

    def get_empty_block(self):
        F = self.blocking_factor
        empty_rec = self.get_empty_rec()
        data = [empty_rec] * F
        return Block(F, data, F)

    def init_file(self):
        with open(self.filename, "wb") as f:
            # blok 1#
            block = self.get_empty_block()
            block.b = -1
            block.n = 1
            self.write_block(f, block)
            # blokovi od 2 na dalje
            for i in range(1, self.b - 1):
                block = self.get_empty_block()
                block.b = i - 1
                block.n = i + 1
                self.write_block(f, block)
            block = self.get_empty_block()
            block.b = self.b - 1
            block.n = -1
            self.write_block(f, block)
        self.save_E()

    def write_record(self, f, rec):
        binary_data = self.record.dict_to_encoded_values(rec)
        f.write(binary_data)

    def read_record(self, f):
        binary_data = f.read(self.record_size)

        if len(binary_data) == 0:
            return None

        return self.record.encoded_tuple_to_dict(binary_data)

    def print_file(self):
        with open(self.filename, "rb") as f:
            for i in range(self.b):
                block = self.read_block(f)
                print("Bucket {}".format(i+1))
                print(block)

    def find_last_in_chain(self, f, u_block, u_syllable):
        f.seek(u_block * self.block_size)
        block = self.read_block(f)
        syllable = block.data[u_syllable]

        while syllable["next block id"] != -1:
            u_block, u_syllable = syllable["next block id"], syllable["next syllable id"]
            f.seek(u_block * self.block_size)
            block = self.read_block(f)
            syllable = block.data[u_syllable]
        return u_block, u_syllable

    def find_last_free_block(self, f):
        f.seek(self.E * self.block_size)
        block = self.read_block(f)
        n = -1

        while block.n != -1:
            n = block.n
            f.seek(n * self.block_size)
            block = self.read_block(f)
        return n

    def find_next_free(self, f, block):
        i = 0
        prev_n = None
        while block.e <= 0:
            if i < self.b:
                return None
            f.seek(block.n * self.block_size)
            prev_n = block.n
            block = self.read_block(f)
            i += 1
        return prev_n

    def insert_record(self, rec):
        id = rec.get("id")
        block_idx = self.hash(id)

        with open(self.filename, "rb+") as f:
            f.seek(block_idx * self.block_size)
            main_block = self.read_block(f)

            i = 0
            while i < self.blocking_factor and main_block.data[i].get("status") != -1:
                if main_block.data[i].get("id") == id:
                    if main_block.data[i].get("status") == 1:
                        print("Already exists with ID {}".format(id))
                    else:
                        break
                i += 1

            if i == self.blocking_factor:
                self.__insert_overflow(f, rec, main_block, block_idx)
                return

            # ukoliko nije prethodno postavljeno u, znaci nije bilo prethodnika
            if main_block.u_block == -1 or main_block.u_syllable == -1:
                main_block.u_block = block_idx
                main_block.u_syllable = i
                f.seek(block_idx * self.block_size)
                self.write_block(f, main_block)
            # ili ukoliko je bilo prethodnika nadji poslednji
            else:
                # prethodni slog pokazuje na trenutni
                previous_block_indx, previous_syllable_indx = self.find_last_in_chain(f, main_block.u_block,
                                                                                      main_block.u_syllable)
                f.seek(previous_block_indx * self.block_size)
                previous_block = self.read_block(f)
                previous_block.data[previous_syllable_indx]["next block id"] = block_idx
                previous_block.data[previous_syllable_indx]["next syllable id"] = i
                f.seek(previous_block_indx * self.block_size)
                self.write_block(f, previous_block)

            # ucitavamo opet jer smo mozda bas taj blok izmenili
            f.seek(block_idx * self.block_size)
            main_block = self.read_block(f)

            # dodajemo novi slog
            main_block.data[i] = rec

            # smanjuje se kapacitet za 1
            main_block.e -= 1

            # postavljanje novog E ukoliko pokazuje na bas ovaj blok
            if self.E == block_idx and main_block.e <= 0:
                self.E = main_block.n
                self.save_E()

            f.seek(block_idx * self.block_size)
            self.write_block(f, main_block)

            # kapacitet je popunjen
            if main_block.e <= 0:
                prev_indx = main_block.b
                next_indx = main_block.n
                # prevezemo tako da prethodni pokazuje na sledeci maticnog
                if prev_indx != -1:
                    f.seek(prev_indx * self.block_size)
                    prev_block = self.read_block(f)
                    prev_block.n = main_block.n
                    f.seek(-self.block_size, 1)
                    self.write_block(f, prev_block)
                # prevezemo tako da sledeci blok pokazuje na prethodni maticnog
                if next_indx != -1:
                    f.seek(next_indx * self.block_size)
                    next_block = self.read_block(f)
                    next_block.b = main_block.b
                    f.seek(-self.block_size, 1)
                    self.write_block(f, next_block)
                main_block.b = -1
                main_block.n = -1

            #  zapisivanje bloka
            f.seek(block_idx * self.block_size)
            self.write_block(f, main_block)

    def __insert_overflow(self, f, rec, main_block, main_block_idx):
        if self.E == -1:
            print("File is full")
            return None
        new_block_idx = self.E
        # nalazi se nov slobodan baket
        f.seek(new_block_idx * self.block_size)
        block = self.read_block(f)
        i = 0
        while i < self.blocking_factor and block.data[i].get("status") != -1:
            if block.data[i].get("id") == rec["id"]:
                if block.data[i].get("status") == 1:
                    print("Already exists with ID {}".format(id))
                    return None
            i+=1

        # ukoliko nije prethodno postavljeno u, znaci nije bilo prethodnika
        if main_block.u_block == -1 or main_block.u_syllable == -1:
            main_block.u_block = new_block_idx
            main_block.u_syllable = i
            f.seek(main_block_idx * self.block_size)
            self.write_block(f, main_block)
        # ili ukoliko je bilo prethodnika nadji poslednji
        else:
            # prethodni slog pokazuje na trenutni
            previous_block_indx, previous_syllable_indx = self.find_last_in_chain(f, main_block.u_block,
                                                                                  main_block.u_syllable)
            f.seek(previous_block_indx * self.block_size)
            previous_block = self.read_block(f)
            previous_block.data[previous_syllable_indx]["next block id"] = new_block_idx
            previous_block.data[previous_syllable_indx]["next syllable id"] = i
            f.seek(-self.block_size, 1)
            self.write_block(f, previous_block)

        # ucitavamo opet jer smo mozda bas taj blok izmenili
        f.seek(new_block_idx * self.block_size)
        block = self.read_block(f)

        # dodajemo nov slog
        block.data[i] = rec

        # smanjuje se kapacitet za 1
        block.e -= 1

        # postavljanje novog E ukoliko pokazuje na bas ovaj blok
        if self.E == new_block_idx and block.e <= 0:
            self.E = block.n
            self.save_E()

        # kapacitet je popunjen
        if block.e <= 0:
            prev_indx = block.b
            next_indx = block.n
            # prevezemo tako da prethodni pokazuje na sledeci maticnog
            if prev_indx != -1:
                f.seek(prev_indx * self.block_size)
                prev_block = self.read_block(f)
                prev_block.n = main_block.n
                f.seek(-self.block_size, 1)
                self.write_block(f, prev_block)
            # prevezemo tako da sledeci blok pokazuje na prethodni maticnog
            if next_indx != -1:
                f.seek(next_indx * self.block_size)
                next_block = self.read_block(f)
                next_block.b = main_block.b
                f.seek(-self.block_size, 1)
                self.write_block(f, next_block)
            block.b = -1
            block.n = -1
        #  zapisivanje bloka
        f.seek(new_block_idx * self.block_size)
        self.write_block(f, block)

    def find_by_id(self, id):
        block_idx = self.hash(id)

        with open(self.filename, "rb+") as f:
            f.seek(block_idx * self.block_size)
            main_block = self.read_block(f)
            u_block, u_syllable = main_block.u_block, main_block.u_syllable
            if u_block == -1 or u_syllable == -1:
                return None
            f.seek(u_block * self.block_size)
            block = self.read_block(f)
            syllable = block.data[u_syllable]

            # ako je bas to taj slog
            if syllable["id"] == id and syllable["status"] == 1:
                return u_block, u_syllable

            # ako ne gledamo sledece
            while syllable["next block id"] != -1:
                u_block, u_syllable = syllable["next block id"], syllable["next syllable id"]
                f.seek(u_block * self.block_size)
                block = self.read_block(f)
                syllable = block.data[u_syllable]
                if syllable["id"] == id and syllable["status"] == 1:
                    return u_block, u_syllable
            return None

    def delete_by_id(self, id):
        found = self.find_by_id(id)

        if not found:
            print("No record with such id exists")
            return None

        block_idx = found[0]
        rec_idx = found[1]

        with open(self.filename, "rb+") as f:
            # brisanje
            f.seek(block_idx * self.block_size)
            block = self.read_block(f)
            record = block.data[rec_idx]
            block.data[rec_idx] = self.get_empty_rec()
            block.e += 1

            # ako je blok bio pun, sada ga smestamo na kraj lanca slobodnih baketa
            if block.e - 1 <= 0:
                last_free_idx = self.find_last_free_block(f)
                if last_free_idx == -1:
                    self.E = block_idx
                    self.save_E()
                f.seek(last_free_idx * self.block_size)
                last_free = self.read_block(f)
                last_free.n = block_idx
                f.seek(-self.block_size, 1)
                self.write_block(f, last_free)

                block.b = last_free_idx

            # sacuvamo izmenu
            f.seek(block_idx * self.block_size)
            self.write_block(f, block)

            main_block_idx = self.hash(id)
            f.seek(main_block_idx * self.block_size)
            main_block = self.read_block(f)

            # ukoliko je u pokazivalo bas na ovaj blok, resetuje se, i to znaci da nije bilo prethodnika
            if main_block.u_block == block_idx and main_block.u_syllable == rec_idx:
                main_block.u_block = -1
                main_block.u_syllable = -1
                f.seek(main_block_idx * self.block_size)
                self.write_block(f, main_block)
            # ili ukoliko je bilo prethodnika nadji poslednji
            else:
                previous_block_idx, previous_syllable_idx = self.find_previous_in_chain(f, main_block.u_block,
                                                                                          main_block.u_syllable,
                                                                                          block_idx,
                                                                                       rec_idx)
                # ucitamo prethodni
                f.seek(previous_block_idx * self.block_size)
                previous_block = self.read_block(f)

                # podatke sloga smo zapamtili u record i odatle vidimo koji je sledeci slog bio
                next_block_idx = record["next block id"]
                next_syllable_idx = record["next syllable id"]

                # prevezemo sledeci izbrisanog sloga
                previous_block.data[previous_syllable_idx]["next block id"] = next_block_idx
                previous_block.data[previous_syllable_idx]["next syllable id"] = next_syllable_idx
                # sacuvamo
                f.seek(previous_block_idx * self.block_size)
                self.write_block(f, previous_block)



    def find_previous_in_chain(self, f, u_block, u_syllable, block_idx, rec_idx):
        f.seek(u_block * self.block_size)
        block = self.read_block(f)
        syllable = block.data[u_syllable]

        while syllable["next block id"] != block_idx and syllable["next syllable id"] != rec_idx:
            u_block, u_syllable = syllable["next block id"], syllable["next syllable id"]
            f.seek(u_block * self.block_size)
            block = self.read_block(f)
            syllable = block.data[u_syllable]
        return u_block, u_syllable


if __name__ == '__main__':
    rec = Record(ATTRIBUTES, FMT, CODING)
    fn = "../data/sample.dat"
    binary_file = LinkedHashFile(fn, rec, F, B, struct.calcsize(BLOCK_HEADER_FMT))
    binary_file.init_file()
    with open(fn, "rb+") as f:
        attributes = ["id", "account number", "date", "description of purpouse", "ammount", "status", "next block id", "next syllable id"]
        values = [10, "12345", "5.5.2021.", "uplata", 10000, 1, -1, -1]

        for i in range(11):
            values[0] += 9
            rec = {attributes[i]: values[i] for i in range(8)}
            binary_file.insert_record(rec)

        values[0] = 9
        rec = {attributes[i]: values[i] for i in range(8)}
        binary_file.insert_record(rec)

        values[0] = 18
        rec = {attributes[i]: values[i] for i in range(8)}
        binary_file.insert_record(rec)
        print(binary_file.E)
        binary_file.print_file()


    binary_file.delete_by_id(28)
    binary_file.print_file()
    # binary_file.delete_by_id(37)
    binary_file.delete_by_id(64)
    binary_file.print_file()



