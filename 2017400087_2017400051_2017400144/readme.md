
# Halo Software
Halo Software is a program to manage different species living in the planet E226 − S187. You can create species, list or delete them. You can create individuals, list, search for, update or delete them. 

## Usage

Use the code below to run haloSoftware in python 3.

```bash
python3 2017400051_2017400097_2017400144/src/haloSoftware.py inputFile outputFile
```
Input file should only consist of following commands: 

```bash
register user <user_name> <password> <password_repeat>
login <user_name> <password>
logout
create type <type_name> <number_of_fields> <field1_value> <field2_value>....
delete type <type_name> 
inherit type <target_type_name> <source_type_name> <additional_field1_value> <additional_field2_value>....
list type
create record <type_name> <primary_key> <field1_value> <field2_value>....
delete record <type_name> <primary_key>
update record <type_name> <primary_key> <field2_value> <field3_value>....
search record <type_name> <primary_key>
list record <type_name>
```
