import sqlite3
from datetime import datetime

con = sqlite3.connect('data.db')
cur = con.cursor()
every = cur.execute('''SELECT * FROM Trainings''').fetchall()
for i in every:
    date = datetime.strptime(i[2][:-3], '%Y-%m-%d %H:%M')
    if datetime.now() > date:
        cur.execute('''DELETE FROM Trainings WHERE id = ?''', (i[0],))
        con.commit()
        cur.execute('''DELETE FROM user_to_training WHERE training_id=?''', (i[0],))
        con.commit()
