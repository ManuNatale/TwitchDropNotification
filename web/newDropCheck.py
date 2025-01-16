import sendEmail
import telegramSend

import threading
import time
import sys
import configparser

import firebase_admin
from firebase_admin import db
from flask import Flask, render_template, request

# read config
# Create a ConfigParser object
config = configparser.ConfigParser()

# Read the configuration file
config.read('./config.ini')

# Access values from the configuration file
databaseURL = config.get('General', 'databaseURL')
firebaseCredFile = config.get('General', 'firebaseCredFile')
personnalTelegramID = config.get('General', 'personnalTelegramID')
personnalEmail = config.get('Email', 'personnalEmail')

#cred_obj = firebase_admin.credentials.Certificate(firebaseCredFile)
#default_app = firebase_admin.initialize_app(cred_obj, {
#    'databaseURL':databaseURL
#    })

def main(o):
    print("Starting users drop checking")
    time.sleep(3)
    
    while(True):
        print("New iteration of newDropCheck")
        try:
            usersDbGet = db.reference("/users/").get()
            usersDbRef = db.reference("/users/")
            gamesDbGet = db.reference("/games/").get()
            
            
            # Iterate users to get the data
            for user, userData in usersDbGet.items():
                #print(user)
                # user specific zone:
                gamesToSendNotif={}
                
                for game in userData["games"]:
                    # check if game value on the user and game live time on the game match, if don't match add it to send game notif
                    if userData["games"].get(game)!= gamesDbGet[game].get("gameLiveTime"):
                        gamesToSendNotif.update({game: gamesDbGet[game].get("gameLiveTime")})
                        
                        
                # set the value if the game is sent to the live time value
                userdbGamesRef=db.reference(f"/users/{user}/games")
                userdbGamesData=userdbGamesRef.get()
                for game in list(gamesToSendNotif):
                    userdbGamesData[game]=gamesToSendNotif[game]
                    # if game is now to not live, remove it from the notif send dict
                    if gamesToSendNotif[game]=="Not Live":
                        del gamesToSendNotif[game]
                        
                
                # push to the data base
                userdbGamesRef.update(userdbGamesData)
            
                #if no games to send notif continue
                if len(gamesToSendNotif)==0:
                    #print("No game to update")
                    continue
                
                # create the text for the notif email
                notifTextEmail="<HTML><BODY><b>Active drop campaigns:</b><br><br>"
                
                notifTextTelegram="*Active drop campaigns:*\n\n"
                
                #add each game to the notif text
                for game in gamesToSendNotif:
                    #email
                    gameInfoEmail=f"<HTML><BODY><b>{game}</b>: {gamesToSendNotif.get(game)}<br>"
                    notifTextEmail += gameInfoEmail
                    #telegramSend
                    gameInfoTelegram=f"*{game}*: {gamesToSendNotif.get(game)}\n".replace(r"-", r"\-").replace(r"+", r"\+") # need to be a raw string "r" or it thorw an error
                    notifTextTelegram += gameInfoTelegram

                #for telegramSend
                notifTextTelegram += "\n/help for more"
                 
                # add unsubscribe link
                unsubscribeLinkEmail=f'<HTML><a href="https://twitchdropnotif.pythonanywhere.com/unsubscribe?id={user}" target="_blank">Unsubscribe</a>  |  '
                notifTextEmail += unsubscribeLinkEmail
                
                # add edit preferences link
                preferencesLinkEmail=f'<HTML><a href="https://twitchdropnotif.pythonanywhere.com/?id={user}" target="_blank">Edit preferences</a>'
                notifTextEmail += preferencesLinkEmail
                
                #print(f"Email text: {notifTextEmail}")
                #print(f"Telegram text: {notifTextTelegram}")
                
                if userData["email"] != "":
                    #sendEmail.Send(userData["email"], "Active Twitch Drop campaigns", notifTextEmail)
                    print(f"email sent {userData['email']}")
                    
                if userData["telegram"] != "":
                    msgs = [notifTextTelegram[i:i + 4095] for i in range(0, len(notifTextTelegram), 4095)]
                    for text in msgs:
                        print(f"My text len {len(text)}")
                        #telegramSend.send(userData["telegram"], text)
                        threading.Thread(target=telegramSend.send, args=(userData["telegram"], text)).start()
                        print(f"telegram sent {userData['telegram']}")
                
            #sys.exit()
            print("Waiting before next newDropCheck")
            time.sleep(900)
            
        except Exception as e:
            print(e)
            sendEmail.Send(personnalEmail, "Error in sendEmail While loop", f"Error: {e}")
            telegramSend.send(personnalTelegramID, f"Error in newDropCheck: {e}")
            time.sleep(3600)
            

#main(1)