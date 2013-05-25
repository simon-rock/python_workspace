#database.py

import sys, shelve

def store_person(db):
    """
    QUery user for data and store it in the shelf object
    """

    pid = raw_input('Entry unique ID number: ')
    person = {}
    person['name'] = raw_input('Enter name: ')
    person['age']  = raw_input('Enter age: ')
    person['phone']= raw_input('Enter phone number: ')

    db[pid] = person

def lookup_person(db):
    """
    Query user for ID and desired field. and fetch the corresponding data from
    the shelf object
    """

    pid = raw_input('Enter ID number: ')
    field = raw_input('What would you like to know? (name, age, phone) ')
    field = field.strip().lower()
    print field.capitalize() + ':', \
          db[pid][field]

def print_help():
    print 'The avaliable: command are'
    print 'store : store information about a person'
    print 'lookup: looks up a person from ID number'
    print 'quit: save and exit'
    print '?     : print this message'

def enter_command():
    cmd = raw_input('Enter command (? for help):')
    cmd = cmd.strip().lower()
    return cmd

def main():
    database = shelve.open('c:\\database.dat')
    try:
        while True:
            cmd = enter_command()
            if cmd == 'store':
                store_person(database)
            elif cmd == 'lookup':
                lookup_person(database)
            elif cmd == '?':
                print_help()
            elif cmd == 'quit':
                return
    finally:
        database.Close()
if __name__ == '__main__':
    main()
