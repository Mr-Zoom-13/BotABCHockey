# BotABCHockey
Commercial bot for Hockey school in Moscow. 
Allows you to create workouts, track logs, view people's records. Implemented accounts for administrators, coaches and clients
## Where can I watch?
You can find it in Telegram https://t.me/abchockeybot  
Or setup on your local machine
## Instrcutions for setupping
### First step
Clone this repository, create config.py in the root of project.  
Example for config.py:
```py
id_channel = -9999999999
id_chat = -999999999999
id_private_chat = -99999999999
id_tech_chat = -9999999999999
bot_token = 'sfkkfsan214kmsfmk3m325n2kssfm'
admins = [1181124378, 1234, 567]
trainers = [12342, 3121412, 75737345]
```
### Second step
Install all libraries by this command in the root:
```
pip3 install -r requirements.txt
```
### Third step
Run project by this command in the root:
```
python3 app.py
```  
Great! The bot is running and you can check on your bot(whos token is used)
## Feedback
If you want to talk with me(who created this bot) or suggest changes you can find me in TG: https://t.me/Zeifert_Alex 
