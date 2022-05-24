import os
import sys
import time
from os import path

system_catalog = []
if path.exists("system_catalog.txt"):
    system_catalog_file = open("system_catalog.txt", "r+")
    for line in system_catalog_file:
        line_split = line.split()
        line_list = []
        for p in line_split:
            line_list.append(p)
        system_catalog.append(line_list)
    system_catalog_file.close()

output_dir = sys.argv[2]
if os.path.exists(output_dir):
    os.remove(output_dir)
out_file = open(output_dir, "a")
type_file_map = {}

logged_in = False
logged_user = "null"

def adjust_value_size(value):
    value = str(value)
    while len(value)<20:
        value = " " + value
    return value


class File:

    attributes = []
    global type_file_map
    def __init__(self, no_of_pages, file_id, type, max_record, min_record, no_of_fields):
        type_not_adjusted = type
        not_adjusted_file_id = file_id
        no_of_pages = adjust_value_size(no_of_pages)
        file_id = adjust_value_size(file_id)
        type = adjust_value_size(type)
        max_record = adjust_value_size(max_record)
        min_record = adjust_value_size(min_record)
        no_of_fields = adjust_value_size(no_of_fields)

        self.no_of_pages = no_of_pages
        self.file_id = file_id
        self.type = type
        self.max_record = max_record
        self.min_record = min_record
        self.no_of_fields = no_of_fields

        self.header = no_of_pages + file_id + type + max_record + min_record + no_of_fields + "\n"
        self.file_name = open(type_not_adjusted + str(not_adjusted_file_id)+".txt", "a")
        type_file_map[type_not_adjusted].append(type_not_adjusted + str(not_adjusted_file_id) + ".txt")
        self.file_name.write(self.header)
        self.file_name.close()

    def fill_attributes(self, attribute_names):
        for i in attribute_names:
            File.attributes.append(i)


class Page:

    def __init__(self, no_of_records, page_id, max_record, min_record):
        no_of_records = adjust_value_size(no_of_records)
        page_id = adjust_value_size(page_id)
        max_record = adjust_value_size(max_record)
        min_record = adjust_value_size(min_record)

        self.no_of_records = no_of_records
        self.page_id = page_id
        self.max_record = max_record
        self.min_record = min_record

        self.header = no_of_records + page_id + max_record + min_record


def create_file(type_name, file_id, number_of_fields, fields):
    file_obj = File(0, file_id, type_name, -1, 2**20 - 1, number_of_fields)
    file_obj.fill_attributes(fields)


def create_type(type_name, number_of_fields, fields):
    global system_catalog, type_file_map

    if len(fields) != int(number_of_fields):
        return "failure"
    type_file_map[type_name] = []
    file_obj = File(0, 1, type_name, 0, 2**20-1, number_of_fields)
    file_obj.fill_attributes(fields)

    for ind, field in enumerate(fields):
        system_catalog.append([field, type_name, "string", str(ind+1)])
    return "success"

def output_formatter(s):
    str_list = s.split()
    new_str = ""
    for st in str_list:
        new_str += st + " "
    return new_str


def list_type():
    global system_catalog, out_file
    typez = []
    for line in system_catalog:
        typez.append(line[1])
    types = set(sorted(typez))
    for t in types:
        if t == "system_catalog":
            continue
        out_file.write(t + "\n")
    return "success"


def inherit_type(type_name, parent_name, fieldz):
    global system_catalog, type_file_map
    if not parent_name in type_file_map:
        return "failure"
    parents_columns = []
    fields = []
    for line in system_catalog:
        if line[1] == parent_name:
            parents_columns.append(line[0])
    parents_columns.extend(fieldz)
    fields.extend(parents_columns)
    type_file_map[type_name] = []

    file_obj = File(0, 1, type_name, 0, 2 ** 20 - 1, len(fields))
    file_obj.fill_attributes(fields)

    for ind, field in enumerate(fields):
        system_catalog.append([field, type_name, "string", str(ind + 1)])
    return "success"

def delete_type(type_name):
    global type_file_map, system_catalog
    if not type_name in type_file_map:
        return "failure"
    file_names = type_file_map[type_name]
    for file_name in file_names:
        os.remove(file_name)

    for x in system_catalog:
        if x[1] == type_name:
            system_catalog.remove(x)

    del type_file_map[type_name]
    return "success"

def search_record(type_name, primary_key):
    global type_file_map
    if not type_name in type_file_map:
        return "failure"
    record_found = "failure"
    primary_key = int(primary_key)
    record_files = type_file_map[type_name][:]
    for r in record_files:
        opened_file = open(r, "r+")
        file_header = opened_file.read(120)
        no_of_pages = int(file_header[0:20])
        offset = 122
        for i in range(no_of_pages):
            opened_file.seek(offset + 2504*i, 0)
            page_content = opened_file.read(2502)
            no_of_records = int(page_content[:20])
            pmin = int(page_content[60:80])
            tmp = page_content.splitlines()
            records_of_page = tmp[1:]
            if(primary_key < pmin):
                continue
            else:
                for j in range(no_of_records):
                    record_key = int(records_of_page[j][20:40])
                    if(record_key == primary_key):
                        out_file.write(output_formatter(records_of_page[j]) + "\n")
                        record_found = "success"
                        break
        opened_file.close()
        return record_found

def update_record(type_name, primary_key, fields):
    global type_file_map
    if not type_name in type_file_map:
        return "failure"
    primary_key = int(primary_key)
    record_files = type_file_map[type_name][:]
    values_new = ''
    record_found = "failure"
    for v in fields:
        values_new += adjust_value_size(v)
    for r in record_files:
        opened_file = open(r, "r+")
        file_header = opened_file.read(120)
        no_of_pages = int(file_header[0:20])
        offset = 122
        for i in range(no_of_pages):
            opened_file.seek(offset + 2504*i, 0)
            page_content = opened_file.read(2502)
            p_header = page_content[0:80]
            no_of_records = int(page_content[:20])
            pmin = int(page_content[60:80])
            tmp = page_content.splitlines()
            records_of_page = tmp[1:]
            if(primary_key < pmin):
                continue
            else:
                new_rec = ""
                for j in range(no_of_records):
                    record_key = int(records_of_page[j][20:40])
                    if(record_key == primary_key):
                        temp_rec = records_of_page[j]
                        new_rec = temp_rec[:40] + values_new
                        records_of_page.remove(temp_rec)
                        records_of_page.insert(j, new_rec)
                        record_found = "success"
                        break
                opened_file.seek(offset + 2504 * i, 0)
                opened_file.write(p_header + "\n")
                for r in records_of_page:
                    opened_file.write(r + "\n")
        opened_file.close()
        return record_found


def update_file_header(type_name, file_id):
    global type_file_map
    opened_file = open(type_file_map[type_name][file_id-1], "r+")
    opened_file.seek(0, 0)
    file_header = opened_file.read(120)
    print("mahmut", file_header)
    no_of_pages = int(file_header[:20])
    print(no_of_pages)
    opened_file.seek(122, 0)
    first_page = opened_file.read(2502)
    print(first_page)
    maxr = first_page[40:60]
    print(maxr)
    opened_file.seek(0,0)
    opened_file.seek(122 + 2504*(no_of_pages-1), 0)
    last_page = opened_file.read(2502)
    print(last_page)
    minr = last_page[60:80]
    print(minr)

    new_file_header = file_header[:60] + maxr + minr + file_header[100:]
    opened_file.seek(0, 0)
    opened_file.write(new_file_header)


def delete_page(type_name, primary_key):
    global type_file_map
    primary_key = int(primary_key)
    record_files = type_file_map[type_name][:]
    for r in record_files:
        opened_file = open(r, "r+")
        file_header = opened_file.read(120)
        file_id = int(file_header[20:40])
        file_txt = type_name + str(file_id) + ".txt"
        no_of_pages = int(file_header[0:20])
        offset = 122
        for i in range(no_of_pages):
            opened_file.seek(offset + 2504 * i, 0)
            page_content = opened_file.read(2502)
            no_of_records = int(page_content[:20])
            pheader = page_content[:80]
            page_id = int(page_content[20:40])
            pmin = int(page_content[60:80])
            tmp = page_content.splitlines()
            records_of_page = tmp[1:]
            if (primary_key < pmin):
                continue
            else:
                for j in range(no_of_records):
                    record_key = int(records_of_page[j][20:40])
                    if (record_key == primary_key): # we are at the correct record
                        to_be_del_record = records_of_page[j]
                        records_of_page.remove(to_be_del_record)
                        if no_of_records -1 == 0: #this page is now empty
                            if no_of_pages -1 == 0: #this file is now empty
                                type_file_map[type_name].remove(file_txt)
                                opened_file.close()
                                os.remove(file_txt)
                            else: #only remove the last page of file
                                opened_file.seek(offset + 2504 * i, 0)
                                opened_file.truncate(offset + 2504 * (no_of_pages-1))
                                file_header = adjust_value_size(int(no_of_pages-1)) + file_header[20:]
                                opened_file.seek(0, 0)
                                opened_file.write(file_header)
                        elif no_of_records <= 10 and no_of_pages -1 == i:
                            return # code sth !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

                        else:#page is not empty, we should move other entries upwards.
                            page_current = page_id
                            next_page_id = page_id+1
                            opened_file.seek(offset + 2504 * page_current, 0)
                            next_page_records = opened_file.read(2502).splitlines()
                            next_pheader = next_page_records[0]
                            first_of_next = next_page_records[1]
                            next_page_record_no = next_pheader[:20]
                            if next_page_record_no == 1: #next page has only one record
                                records_of_page.append(first_of_next)
                                opened_file.close()
                                opened_file = open(file_txt, "r+")
                                opened_file.seek(offset + 2504 * (page_current - 1), 0)
                                pbody = pheader[:60] + first_of_next[20:40] + "\n"
                                for rec in records_of_page:
                                    pbody += rec + "\n"
                                pbody += "\n"
                                opened_file.write(pbody)
                                opened_file.truncate(offset + 2504 * page_current)
                            else:
                                records_of_page.append(first_of_next)
                                opened_file.close()
                                opened_file = open(file_txt, "r+")
                                opened_file.seek(offset + 2504 * (page_current - 1), 0)
                                pbody = pheader[:60] + first_of_next[20:40] + "\n"
                                for rec in records_of_page:
                                    pbody += rec + "\n"
                                pbody += "\n"
                                opened_file.write(pbody)
                                while next_page_id < no_of_pages:
                                    return #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                                    









        opened_file.close()

def create_page(page_id, file_name, record):
    op_fil = open(file_name, "a")
    dummy_line = " "*240 + "\n"
    op_fil.write(dummy_line*10 + "\n")
    op_fil.close()

    opened_file = open(file_name, "r+")
    opened_file.seek(0,0)
    f_header = opened_file.read(120)
    no_of_fields = int(f_header[100:])
    if not record:
        p_header = adjust_value_size("0") + adjust_value_size(page_id) + adjust_value_size(str(-1)) + adjust_value_size(str(2 ** 20 - 1)) + "\n"
        p_body = ""
        for i in range(10):
            p_body += (" " * 240 + "\n")
        p_body += "\n"
        opened_file.seek(122 + (page_id-1)*2504, 0)
        opened_file.write(p_header + p_body)
    else:
        p_header = adjust_value_size("1") + adjust_value_size(page_id) + adjust_value_size(record[20:40]) + adjust_value_size(record[20:40]) + "\n"
        p_body = record
        print(len(record))
        if(len(record) < 240):
            for i in range(10 - no_of_fields):
                p_body += " " * 20
        p_body += "\n"
        for i in range(9):
            p_body += (" " * 240 + "\n")
        p_body += "\n"
        print("page uzunluğu = ", len(p_body)+len(p_header))
        opened_file.seek(122 + (page_id-1)*2504, 0)
        opened_file.write(p_header + p_body)
    print("body ", len(p_body))
    print("header ", len(p_header))
    print(p_header+p_body)
    opened_file.seek(0, 0)
    file_header = opened_file.read(120)
    print(file_header)
    new_file_header = adjust_value_size(str(page_id)) + file_header[20:]
    opened_file.seek(0, 0)
    opened_file.write(new_file_header)
    print(new_file_header)
    opened_file.close()


def values_formatter(record_string, no_of_fields):
    values = []
    for i in range(no_of_fields+2):
        if i == 0:
            continue
        else:
            values.append(record_string[i*20:(i+1)*20])
    return values


def create_record(type_name, values):
    global type_file_map
    for ind, val in enumerate(values):
        values[ind] = adjust_value_size(val)

    # string format of record to be inserted
    values.insert(0, adjust_value_size("E226-S187"))
    record_to_be_inserted = ""
    for v in values:
        record_to_be_inserted += adjust_value_size(v)

    file_list = type_file_map[type_name][:]
    primary_key = int(values[1])
    print(record_to_be_inserted)
    for f in file_list: # traverses file names' list
        opened_file = open(f, "r+")
        opened_file.seek(0, 0)
        file_header = opened_file.read(120)
        file_id = int(file_header[20:40])
        no_of_pages = int(file_header[:20])
        no_of_fields = int(file_header[100:])

        opened_file.close()
        # creating an empty page if no pages exist
        if no_of_pages == 0:
            create_page(1, (type_name + str(file_id))+".txt", record_to_be_inserted)
            update_file_header(type_name, file_id)
            return "success"
        opened_file = open(type_name + str(file_id)+".txt", "r+")
        maxr = int(file_header[60:80])
        minr = int(file_header[80:100])
        print(primary_key, minr)

        # take the page, if the page is modified re-write it, else keep iterating
        if minr == primary_key or maxr == primary_key:
            return "failure"

        elif minr < primary_key or file_id == len(type_file_map[type_name]): # record should be inserted in this file

            # 82 + 242*10 = 2502 size of a page, 122 + 2502*i = offset of a page

            for pno in range(no_of_pages):
                offset = 122 + 2504*pno
                opened_file.seek(offset, 0)
                page_string = opened_file.read(2502) #????????????????????????
                print(page_string)
                page_lines = page_string.splitlines()
                pheader = page_lines[0]
                record_lines = page_lines[1:]
                pmax = int(pheader[40:60])
                pmin = int(pheader[60:80])
                p_record_count = int(pheader[:20])

                if pmin == primary_key or pmax == primary_key:
                    return "failure"
                elif pmin < primary_key or pno == no_of_pages-1:
                    if p_record_count < 10:
                        #record_lines.remove("\n")
                        for ind, r in enumerate(record_lines):
                            print(len(r), r)
                            if r == " " * 240 or r == "\n":
                                record_primary_key = -1
                            else:
                                record_primary_key = int(r[20:40])
                            print(primary_key, record_primary_key, " burdayızz", r)
                            if record_primary_key == primary_key:
                                return "failure"
                            if primary_key > record_primary_key:
                                print("tempalcam")
                                tmp_record_lines = []
                                tmp_record_lines.extend(record_lines)
                                for tmp_l in range(10 - no_of_fields):
                                    record_to_be_inserted += " " * 20
                                tmp_record_lines.insert(ind, record_to_be_inserted)

                                p_new_max = tmp_record_lines[0][20:40]
                                p_new_min = tmp_record_lines[p_record_count][20:40]
                                updated_page = adjust_value_size(str(p_record_count+1)) + pheader[20:40] + p_new_max + p_new_min + "\n"
                                for x in tmp_record_lines:
                                    if x == " "*240 or len(x) == 0:
                                        break
                                    if len(x) < 240:
                                        for l in range(10-no_of_fields):
                                            x += " "* 20
                                    updated_page += (x + "\n")
                                for i in range(9-p_record_count):
                                    updated_page += (" "*240 + "\n")
                                updated_page += "\n"
                                print(updated_page)
                                opened_file.seek(offset, 0)
                                opened_file.write(updated_page)
                                opened_file.close()
                                update_file_header(type_name, file_id)

                                return "success"
                            else:
                                continue
                    elif p_record_count == 10:
                        #record_lines.remove("\n")
                        for ind, r in enumerate(record_lines):
                            print(record_lines)
                            if r == " "*240 or r == "\n":
                                record_primary_key = -1
                            else:
                                record_primary_key = int(r[20:40])
                            print(record_primary_key)
                            if record_primary_key == primary_key:
                                return "failure"
                            if primary_key > record_primary_key:
                                record_lines.insert(ind, record_to_be_inserted)
                                replace_record = record_lines[10]
                                record_lines.pop(10)
                                print(record_lines[ind])
                                p_new_max = record_lines[0][20:40]
                                p_new_min = record_lines[9][20:40]
                                print(p_new_max, p_new_min)
                                updated_page = adjust_value_size(str(p_record_count)) + pheader[20:40] + p_new_max + p_new_min + "\n"
                                for x in record_lines:
                                    if x == " " * 240 or len(x) == 0:
                                        break
                                    if len(x) < 240:
                                        print("lengthim budur", len(x))
                                        for l in range(10-no_of_fields):
                                            x += " "* 20
                                    updated_page += (x + "\n")
                                for i in range(9 - p_record_count):
                                    updated_page += (" " * 240 + "\n")
                                updated_page += "\n"
                                print(updated_page)
                                opened_file.seek(offset, 0)
                                opened_file.write(updated_page)

                                record_to_be_inserted = replace_record

                                if pno == 19: # bum, son file son page, if ekle
                                    if len(type_file_map[type_name])-1 == file_id:
                                        create_file(type_name, len(type_file_map[type_name]), 0, 2**20-1)
                                        opened_file.close()
                                        create_page(1, opened_file, record_to_be_inserted)
                                        update_file_header(type_name, len(type_file_map[type_name]) - 1)
                                        update_file_header(type_name, len(type_file_map[type_name]) - 2)
                                        return "success"
                                    else: # son fileda değiliz, diğer file'a geçmemiz lazım
                                        opened_file.close()
                                        update_file_header(type_name, file_id)
                                        values_new = values_formatter(record_to_be_inserted, no_of_fields)
                                        create_record(type_name, values_new)

                                elif no_of_pages != 20 and pno+1 == no_of_pages:
                                    print(record_to_be_inserted)
                                    opened_file.close()
                                    create_page(pno+2, (type_name + str(file_id)+".txt"), record_to_be_inserted)
                                    return "success"
                                else: # there are other pages
                                    print(record_to_be_inserted)
                                    opened_file.close()
                                    update_file_header(type_name, file_id)
                                    values_new = values_formatter(record_to_be_inserted, no_of_fields)
                                    create_record(type_name, values_new)
                                    return "success"

                            else:
                                continue
                else: # page min is larger than record and this is not the last page
                    continue
        else: # files min is larger than record and this is not the last file
            opened_file.close()
            continue


def list_records(type_name):
    global type_file_map, out_file
    if not type_name in type_file_map:
        return "failure"
    files = type_file_map[type_name]
    records = []
    for fname in files:
        f = open(fname, "r")
        f.seek(0, 0)
        f_header = f.read(122)
        no_of_pages = int(f_header[:20])
        for i in range(no_of_pages):
            f.seek(122 + i*2504, 0)
            page = f.read(2502)
            p_no_of_records = int(page[:20])
            records_stream = page.splitlines()
            for j in range(p_no_of_records):
                if j == 0:
                    continue
                records.append(records_stream[j])
    recs_string = ""
    for r in records:
        recs_string += r + "\n"
    out_file.write(recs_string)
    return "success"

def logout():
    global logged_user, logged_in
    if logged_in:
        logged_user = "null"
        logged_in = False
        return "success"
    else:
        return "failure"


def login_user(user_name, password):
    global logged_user, logged_in
    if logged_in:
        return "failure"
    else:
        user_infos_file = open("users.txt", "r+")
        user_infos_file.seek(0,0)
        user_infos = user_infos_file.readlines()
        for u in user_infos:
            u_parsed = u.split()
            if user_name == u_parsed[0] and password == u_parsed[1]:
                logged_in = True
                logged_user = user_name
                return "success"
        return "failure"


def register_user(user_name, password, p_repeat):
    global logged_user, logged_in
    if password != p_repeat:
        return "failure"
    user_infos_file = open("users.txt", "a+")
    for u in user_infos_file:
        u_parsed = u.split()
        if user_name == u_parsed[0]:
            return "failure"
    user_infos_file.write(user_name + " " + password + "\n")
    return "success"

def main():
    global system_catalog, logged_user, logged_in
    if path.exists("type_file_name.txt"):
        type_file_map_file = open("type_file_name.txt", "r+")
        for t in type_file_map_file:
            t_split = t.split()
            t_name = t_split[0]
            type_file_map[t_name] = []
            t_count = t_split[1]
            for i in range(int(t_count)):
                type_file_map[t_name].append(t_name+str(i+1)+".txt")
        type_file_map_file.close()
    file = open(sys.argv[1], "r")
    if len(system_catalog) == 0:
        system_catalog.append(["field_name", "system_catalog", "string", "1"])
        system_catalog.append(["type_name", "system_catalog", "string", "2"])
        system_catalog.append(["type", "system_catalog", "string", "3"])
        system_catalog.append(["position", "system_catalog", "string", "4"])

    linez = []
    for line in file:
        linez.append(line)

    log_file = open("haloLog.csv", "a")
    for tmp in linez:
        txt = tmp.split()
        if txt[0] == "login":
            status = login_user(txt[1], txt[2])
            log_file.write(txt[1] + "," + str(time.time()) + ",login," + status)
            continue
        elif txt[0] == "logout":
            ltmp = logged_user
            status = logout()
            log_file.write(ltmp + "," + str(time.time()) + ",logout," + status)
            continue

        command = txt[0] + " " + txt[1]
        if command == "register user":
            status = register_user(txt[2], txt[3], txt[4])
            log_file.write(logged_user + "," + str(time.time()) + "," + command + " " + txt[2] + "," + status)
            continue

        if logged_in:
            if command == "create type":
                status = create_type(txt[2], txt[3], txt[4:])
                log_file.write(logged_user + "," + str(time.time()) + "," + tmp + "," + status)

            elif command == "delete type":
                status = delete_type(txt[2])
                log_file.write(logged_user + "," + str(time.time()) + "," + tmp + "," + status)
            elif command == "inherit type":
                status = inherit_type(txt[2], txt[3], txt[4:])
                log_file.write(logged_user + "," + str(time.time()) + "," + tmp + "," + status)
            elif command == "list type":
                status = list_type()
                log_file.write(logged_user + "," + str(time.time()) + "," + tmp + "," + status)
            elif command == "create record":
                status = create_record(txt[2], txt[3:])
                log_file.write(logged_user + "," + str(time.time()) + "," + tmp + "," + status)
            elif command == "list record":
                status = list_records(txt[2])
                log_file.write(logged_user + "," + str(time.time()) + "," + tmp + "," + status)
            elif command == "update record":
                status = update_record(txt[2], txt[3], txt[4:])
                log_file.write(logged_user + "," + str(time.time()) + "," + tmp + "," + status)
            elif command == "search record":
                status = search_record(txt[2], txt[3])
                log_file.write(logged_user + "," + str(time.time()) + "," + tmp + "," + status)
        else:
            log_file.write(logged_user + "," + str(time.time()) + "," + tmp + "," + "failure")

    tfmf = open("type_file_name.txt", "w")
    for k, v in type_file_map.items():
        file_count = len(v)
        tfmf.write(k + " " + str(file_count) + "\n")
    tfmf.close()

    system_catalog_file = open("system_catalog.txt", "w")

    sys_cat_str = ""
    for entry in system_catalog:
        for atr in entry:
            sys_cat_str += atr + " "
        sys_cat_str += "\n"
    system_catalog_file.write(sys_cat_str)


if __name__ == '__main__':
    main()