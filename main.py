import os
import getpass
import sqlite3
import time
import csv

import biplist

BACKUPS_DIR = f'C:/users/{getpass.getuser()}/Apple/MobileSync/Backup/'
DATA_DICT = {'sms': ('Library/SMS/sms.db', 'message')}
MESSAGE_DICT = {'is_from_me': 21, 'handle_id': 5,
                'cache_roomnames': 35, 'text': 2}
BOS_TOKEN = '<BOS>'
EOS_TOKEN = '<EOS>'

# Retrieve desired backup


def get_backup():
    backups_arr = []
    for backup in os.listdir(BACKUPS_DIR):
        backup_path = BACKUPS_DIR + backup
        new_dict = {'path': backup_path,
                    'mtime': os.path.getmtime(backup_path)}
        backups_arr.append(new_dict)
    if (len(backups_arr) == 0):
        print('No backups found.')
        return False
    if (len(backups_arr) == 1):
        print('One backup found.')
        return backups_arr[0]

    print('Select a backup from which to retrieve data:')
    i = 0
    for backup in backups_arr:
        i += 1
        print(f'{i}. {backup.get("path")}')
        mtime = time.localtime(backup.get("mtime"))
        print(f'    Last modified on {mtime[1]}/{mtime[2]}/{mtime[0]}')
    target_index = int(input()) - 1
    while len(backups_arr) < target_index < 0:
        print(f'Error, pick an integer between 0-{len(backups_arr)}')
        target_index = int(input()) - 1
    return backups_arr[target_index]


def retrieve_db_path(backup_dir, target_db):
    manifest = f'{backup_dir}/Manifest.db'
    try:
        with sqlite3.connect(manifest) as conn:
            cur = conn.cursor()
            cur.execute(
                'SELECT * FROM Files WHERE relativePath=?', (target_db,))
            dbs = cur.fetchall()
            db_id = dbs[0][0]
        for dirpath, _, filearr in os.walk(backup_dir):
            for filename in filearr:
                if filename == db_id:
                    db_path = f"{dirpath}/{db_id}"
        return db_path
    except:
        print('Error, could not open db (encrypted?)')
        exit()


def retrieve_data(db_path, table):
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute(f'SELECT * FROM {table}')
        return cur.fetchall()


def organize_sms_into_chats(mssgs):
    chats = {}
    group_chats = {}
    for mssg in mssgs:
        gc_id = mssg[MESSAGE_DICT['cache_roomnames']]
        handle_id = mssg[MESSAGE_DICT['handle_id']]
        if gc_id == None:
            if handle_id in chats.keys():
                chats[handle_id].append(mssg)
            else:
                chats[handle_id] = [mssg]
        else:
            if gc_id in group_chats.keys():
                group_chats[gc_id].append(mssg)
            else:
                group_chats[gc_id] = [mssg]
    return chats, group_chats


def create_prompt_response_pairs(chats):
    corpus_arr = []
    if type(chats) == dict:
        for key in chats.keys():
            for i in range(len(chats[key])):
                mssg = chats[key][i]
                if mssg[MESSAGE_DICT['is_from_me']] == 1 and i != 0:
                    prompt = None
                    for j in range(i):
                        if chats[key][i-j][MESSAGE_DICT['is_from_me']] == 0:
                            prompt = chats[key][i-j]
                            break
                    if type(prompt) == tuple:
                        formatted_prompt = prompt[MESSAGE_DICT['text']].replace(
                            ',', ' ') if type(prompt[MESSAGE_DICT['text']]) == str else ''
                    else:
                        formatted_prompt = ''
                    formatted_response = mssg[MESSAGE_DICT['text']].replace(
                        ',', ' ') if type(mssg[MESSAGE_DICT['text']]) == str else ''
                    formatted_pair = (
                        formatted_prompt, formatted_response)
                    corpus_arr.append(formatted_pair)
    return corpus_arr


def main():
    data = get_backup().get('path')
    db_path = retrieve_db_path(data, DATA_DICT.get('sms')[0])
    mssgs = retrieve_data(db_path, DATA_DICT.get('sms')[1])
    chats, group_chats = organize_sms_into_chats(mssgs)
    corpus = create_prompt_response_pairs(
        chats) + create_prompt_response_pairs(group_chats)
    with open('katie_texts.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=',',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['prompt', 'response'])
        for pair in corpus:
            writer.writerow([pair[0]] + [pair[1]])


main()
