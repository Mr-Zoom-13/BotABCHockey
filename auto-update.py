import sqlite3
from datetime import datetime

con = sqlite3.connect('data.db')
cur = con.cursor()
every = cur.execute('''SELECT * FROM Trainings ORDER BY datetime''').fetchall()
for i in range(len(every)):
    date = datetime.strptime(every[i][2][:-3], '%Y-%m-%d %H:%M')
    print(date.day)
    if datetime.now() > date:
        j = i + 1
        while j < len(every):
            if (datetime.strptime(every[j][2][:-3], '%Y-%m-%d %H:%M').day - date.day) == 1:
                if every[j][5] == 0:
                    break
            j += 1
        if j != len(every):
            cur.execute("""UPDATE Trainings set watching = ? WHERE id = ?""", (1, every[j][0]))
            con.commit()
        cur.execute('''DELETE FROM Trainings WHERE id = ?''', (every[i][0],))
        con.commit()
        cur.execute('''DELETE FROM user_to_training WHERE training_id=?''', (every[i][0],))
        con.commit()
