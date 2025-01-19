from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import sys
import csv
import json
import uuid
import configparser
import threading
import firebase_admin
from firebase_admin import db
from datetime import datetime

import newDropCheck
import telegramSend

# read config
# Create a ConfigParser object
config = configparser.ConfigParser()

# Read the configuration file
config.read('./config.ini')

# Access values from the configuration file
databaseURL = config.get('General', 'databaseURL')
firebaseCredFile = config.get('General', 'firebaseCredFile')
personnalTelegramID = config.get('General', 'personnalTelegramID')

cred_obj = firebase_admin.credentials.Certificate(firebaseCredFile)
default_app = firebase_admin.initialize_app(cred_obj, {
    'databaseURL':databaseURL
    })
    
#Thread start checking new drop for users
threading.Thread(target=newDropCheck.main, args=(1,)).start()

while(True):
    #break
    
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Starting to check live games")
    
    gamesDbRef = db.reference("/games/")
    usersDbRef = db.reference("/users/")
    usersDbGet = db.reference("/users/").get()

    #options = webdriver.ChromeOptions()
    #options.add_argument('--headless=new')
    #options.add_argument("user-data-dir=/home/manu/snap/firefox/common/.mozilla/firefox/")
    #options.add_argument("profile-directory=q2cwcxkf.default") # <-- substitute Profile 3 with your profile name
    #chromedriver_path = './geckodriver'
    #driver = webdriver.Chrome(options=options, service=Service(chromedriver_path))
    
    # Options pour Firefox
    options = Options()
    #options.add_argument("--headless")  # Activer le mode headless
    options.add_argument('-profile')
    options.add_argument('/home/manu/.mozilla/firefox/m0kxyq12.pythonselenium')
    options.set_preference('useAutomationExtension', False)
    profile_path = "/home/manu/.mozilla/firefox/m0kxyq12.pythonselenium"
    #options.set_preference("profile", profile_path)

    # Chemin vers geckodriver
    geckodriver_path = './geckodriver'  # Assurez-vous que geckodriver est dans ce chemin

    # Initialisation du driver
    driver = webdriver.Firefox(service=Service(geckodriver_path), options=options)
    
    driver.get('https://www.twitch.tv/drops/campaigns')
    time.sleep(5)

    # Need to scroll
    try:
        driver.find_element(By.XPATH, "/html/body/div[1]/div/div[1]/div/main/div[1]/div[3]/div/div/div/div/div[5]").location_once_scrolled_into_view
    except:
        pass
    time.sleep(1)

    gamesArray = {}

    try:
        index=1
        while(True):
            gameName = driver.find_element(By.XPATH, f"/html/body/div[1]/div/div[1]/div/main/div[1]/div[3]/div/div/div/div/div[4]/div[{index}]/div[1]/button/div/div[2]/div/h3").text.replace(".", "_%2E_")
            gameLiveTime = driver.find_element(By.XPATH, f"/html/body/div[1]/div/div[1]/div/main/div[1]/div[3]/div/div/div/div/div[4]/div[{index}]/div[1]/button/div/div[3]").text
            if gameName=="":
                continue
            print(gameName)
            print(gameLiveTime)
            gamesArray.update({gameName: {"isLive": 1, "gameLiveTime": gameLiveTime}})
            index += 1
            #time.sleep(0.1)
        
    except Exception as e:
        #print(e)
        if "Log in to Twitch" in driver.page_source:
            telegramSend.send(personnalTelegramID, 'Error trying to access drops campaigns\. Login required')
            time.sleep(3600)
            continue
        else:
            pass

    #print(gamesArray)
    gamesDbRef.update(gamesArray)

    print(f"{index} games drops found")

    totalGames=0

    gamesDbGet = db.reference("/games/").get() # return a dict
    for key, val in gamesDbGet.items():
        totalGames+=1
        print(key)
        if key in gamesArray:
           gamesDbRef.update({key: {"isLive": 1, "gameLiveTime": val["gameLiveTime"]}}) 
        else:
            gamesDbRef.update({key: {"isLive": 0, "gameLiveTime": "Not Live"}})
            
    ###### update users games data-dir
    print(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Updating user games data...")
    usersDbGet = db.reference("/users/").get()

    gamesDbGet = db.reference("/games/").get()
    gamesDbRef = db.reference("/games/")

    for user in usersDbGet:
        userGames=usersDbGet[user]["games"]
        for game in userGames:
            #print(game)
            #print(userGames[game])
            try:
                #print(game)
                #print(gamesDbGet[game]["gameLiveTime"])
                if gamesDbGet[game]["gameLiveTime"] != userGames[game]:
                    #print(f"{game} not live")
                    userGameChangeValue=db.reference(f"/users/{user}/games")
                    userGameChangeValue.update({game: "Not Live"})
            except KeyError as e:
                #if game doesn't exist
                gameToDelete=db.reference(f"/users/{user}/games/{game}")
                gameToDelete.delete()
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} User data updated")


    print(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Total games {totalGames}")
    driver.quit()
    time.sleep(900)


