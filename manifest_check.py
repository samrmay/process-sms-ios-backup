import sqlite3
import os

db = 'data/34a8cef0fdc1b1ca1ce1178f6450ce92c77e3ff0/Manifest.db'
SMS_DB = '3d0d7e5fb2ce288813306e4d4636395e047a3d28'
with sqlite3.connect(db) as conn:
    cur = conn.cursor()
    cur.execute('SELECT * FROM sqlite_master')
    cats = cur.fetchall()
    print(cats)

    cur2 = conn.cursor()
    cur2.execute('SELECT * FROM Files WHERE fileID=?', (SMS_DB,))
    result = cur2.fetchall()
    print(result[0][4])
    print(result[0][4].hex())
