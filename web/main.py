import datetime
import uuid
import threading
import subprocess
import configparser
import asyncio

import telegramSend

import firebase_admin
from firebase_admin import db
from flask import Flask, render_template, request

import pytz


def get_datetime(timestamp):
    return datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S%z")


app = Flask(__name__)

# read config
# Create a ConfigParser object
config = configparser.ConfigParser()

# Read the configuration file
config.read('./config.ini')

# Access values from the configuration file
databaseURL = config.get('General', 'databaseURL')
firebaseCredFile = config.get('General', 'firebaseCredFile')

cred_obj = firebase_admin.credentials.Certificate(firebaseCredFile)
default_app = firebase_admin.initialize_app(cred_obj, {
    'databaseURL':databaseURL
    })


usersDbRef = db.reference("/users/")


@app.route('/')
def index():
    gamesDbGet = db.reference("/games/").get()
    
    # Find user
    user = None
    user_id = request.args.get('id', None)
    if user_id is not None:
        usersDbGet = db.reference(f"/users/").get()
        for user in usersDbGet:
            if user == user_id:
                usersDbGet = db.reference(f"/users/{user_id}").get()
                user = usersDbGet
                userGamesArray=[]
                for userGame in usersDbGet["games"]:
                    print(userGame)
                    userGamesArray.append(userGame.replace("_%2E_", "."))
                
                user["games"]=userGamesArray
                print(user)
                break

    # Games
    games = []
    for availableGame in gamesDbGet.keys():
        games.append(availableGame.replace("_%2E_", "."))

    # Timezones
    timezones = pytz.common_timezones

    return render_template('index.html', user=user, games=games, timezones=timezones)


@app.route('/subscribe', methods=['POST'])
def subscribe():
    
    # Make sure email is valid or a telegram ID is provided
    if 'email' not in request.form or len(request.form['email']) <= 1:
        if 'telegram' not in request.form or len(request.form['telegram']) < 6:
            return render_template('error.html', message='Invalid email or Telegram ID.')
    
    usersDbGet = db.reference("/users/").get()
    
    # Make sure this user is not already subscribed
    for user, data in usersDbGet.items():
        #print(data["telegram"])
        #print(data.values())
        if (request.form['email'] in data["email"] and len(request.form['email']) > 1) or (request.form['telegram'] in data["telegram"] and len(request.form['telegram']) > 1):
            return render_template('error.html', message='This user is already subscribed!')

    games = {}
    for key, value in request.form.items():
        if key.startswith('game_'):
            games.update({key.split('game_')[1]: "Not Live"})
            print(f"Selected game: {key.split('game_')[1]}")
            
    ## if no games are selected error        
    if len(games)==0:
        return render_template('error.html', message='No games where selected!')
            
            
    userId=str(uuid.uuid4())
    user = {userId: {
        'email': request.form['email'],
        'telegram': request.form['telegram'],
        'games': games,
        'created': datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=1))).replace(microsecond=0, tzinfo=datetime.timezone.utc).isoformat(),
        'id': userId
        }
    }

    #firestore_client.collection('users').document(user['email']).set(user)
    usersDbRef.update(user)
    
    #print(user)
    telegramSend.send(request.form['telegram'], 'You have subscribed to notifications\n\n/help for more')

    return render_template('success.html', message='You have subscribed to notifications!')


@app.route('/update', methods=['POST'])
def update():
    
    # Find user
    user = None
    user_id = request.args.get('id', None)
    if user_id is not None:
        usersDbGet = db.reference(f"/users/").get()
        for user in usersDbGet:
            if user == user_id:
                usersDbGet = db.reference(f"/users/{user_id}").get()
                user = usersDbGet
                userGamesArray=[]
                for userGame in usersDbGet["games"]:
                    #print(userGame)
                    userGamesArray.append(userGame)
                
                user["games"]=userGamesArray
                #print(user)
                break
        else:
            return render_template('error.html', message='This user is not subscribed.')
    
    #usersDbGet = db.reference(f"/users/{user_id}").get()
    usersDbGetGames = db.reference(f"/users/{user_id}/games").get()
    
    games = {}
    for key, value in request.form.items():
        if key.startswith('game_'):
            _tempGame=key.split('game_')[1].replace(".", "_%2E_")
            # check if the game already exist on the user
            if _tempGame in usersDbGetGames:
                _tempGameValue=usersDbGetGames[_tempGame]
            else:
                _tempGameValue="Not Live"
            print(usersDbGetGames)
            games.update({_tempGame: _tempGameValue})
            print(f"Selected game: {_tempGame}")
    
    usersDbGames = db.reference(f"/users/{user_id}/games")
    usersDbGames.set(games)

    return render_template('success.html', message='Preferences updated!')


@app.route('/unsubscribe', methods=['GET'])
def unsubscribe():
    
    if "TelegramBot" in request.headers.get("User-Agent", ""):
        return "Preloading not allowed", 403
    
    usersDbRefGet = db.reference("/users/").get()
    
    userId=request.args.get('id')
    if userId in usersDbRefGet:
        print(usersDbRefGet[userId])
        specificUsersDbRef = db.reference(f"/users/{userId}")
        specificUsersDbRef.delete()
        return render_template('success.html', message='You have been unsubscribed')
    else:
        return render_template('error.html', message='This user is not subscribed.')

if __name__ == '__main__':
    subprocess.Popen(["python", "telegramHandle.py"]) # non blocking
    
    app.run('localhost')
    
    
