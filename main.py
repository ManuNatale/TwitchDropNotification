from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import sys
import csv
import json
import uuid
import configparser
import firebase_admin
from firebase_admin import db

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

while(True):
    #break
    
    print("Starting to check live games")
    
    gamesDbRef = db.reference("/games/")
    usersDbRef = db.reference("/users/")
    usersDbGet = db.reference("/users/").get()

    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument("user-data-dir=C:\\Users\\manue\\AppData\\Local\\Google\\Chrome\\User Data")
    options.add_argument("profile-directory=Profile 1") # <-- substitute Profile 3 with your profile name
    chromedriver_path = '.\\chromedriver.exe'
    driver = webdriver.Chrome(options=options, service=Service(chromedriver_path))
    driver.get('https://www.twitch.tv/drops/campaigns')
    time.sleep(5)

    # Need to scroll
    driver.find_element(By.XPATH, "/html/body/div[1]/div/div[1]/div/main/div[1]/div[3]/div/div/div/div/div[5]").location_once_scrolled_into_view
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
    print("\nUpdating user games data...")
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
    print("User data updated")


    print(f"\nTotal games {totalGames}")
    driver.quit()
    time.sleep(900)



