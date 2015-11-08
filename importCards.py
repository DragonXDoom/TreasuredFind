#!/usr/bin/python
#
# importCards.py
#
# Adds all cardData from a JSON file into the database.
#
# Created by Donald Sutherland on 7th November 2015

import sqlite3 as sql
import json
import urllib.request, urllib.parse, urllib.error

ALL_SETS_URL = 'http://mtgjson.com/json/AllSets-x.json'
DATABASE_NAME = 'cardDB.sqlite3'
MANA_SYMBOLS = ['{W}', '{U}', '{B}', '{R}', '{G}',
				'{W/U}', '{R/W}', '{W/B}', '{B/R}', '{G/U}', '{G/W}', '{U/R}', '{R/G}', '{B/G}', '{U/B}',
				'{2/W}', '{2/U}', '{2/B}', '{2/R}', '{2/G}']
COLOURS = ['White','Blue','Black','Red','Green']

db = sql.connect(DATABASE_NAME)
curs = db.cursor()


print("\nAttempting to load AllSets.json locally...")
try:
	with open("AllSets-x.json","r") as readfile:
		AllSets = json.loads(readfile.read())
except FileNotFoundError:
	print("FAILED\n\nAttempting to load AllSets.json online...\n")
	urllib.request.urlretrieve(ALL_SETS_URL, "AllSets-x.json")
	print("Download complete. Loading AllSets.json...")
	try:
		with open("AllSets-x.json","r") as readfile:
			AllSets = json.loads(readfile.read())
	except FileNotFoundError:
		print("FAILED. Try downloading AllSets-x.json manually.")
		AllSets = "FAILED"
		
def insertIntoTable(tableName, values, includeSetId=False):
	curs.execute("PRAGMA table_info({})".format(tableName))
	columnNames = curs.fetchall()
	if not includeSetId:
		columnNames = columnNames[1:]
	columnNames = list(map(lambda x: x[1], columnNames))
	print(columnNames)
	statement = "INSERT INTO {table}({columns}) VALUES ({params})".format(table=tableName,columns=','.join(columnNames),params=','.join(["?" for i in range(len(columnNames))]))
	print(statement)
	curs.execute(statement,values)

def importCard(cardData):
	# Check if card exists already.
	# If so, just add edition
	# Otherwise add both card data and card edition data.
	cardName = cardData.get('name')
	curs.execute("SELECT cardID FROM cardData WHERE cardName = ?",(cardName,))
	result = curs.fetchall()
	if len(result) == 0: # If the card isn't in the card database...
		cardManaCost = cardData.get('manaCost')
		cardCMC = cardData.get('cmc',0)
		cardTypeLine = cardData.get('type')
		cardOracleText = cardData.get('text')
		
		cardPower = cardData.get('power')
		cardToughness = cardData.get('toughness')
		cardLoyalty = cardData.get('loyalty')
		cardHandMod = cardData.get('hand')
		cardLifeMod = cardData.get('life')
		cardIsReserved = cardData.get('reserved')
		cardLayout = cardData.get('layout')
		
		cardLegendText = cardOracleText.replace(cardName, "~")
		# if cardTypeLine.startswith("Legendary"):
		# 	Do something about the gods here.
		
		insertIntoTable('cardData', (cardName,cardManaCost,cardCMC,cardTypeLine,cardOracleText,cardLegendText,cardPower,cardToughness,cardLoyalty,cardHandMod,cardLifeMod,cardIsReserved,cardLayout))
		cardID = curs.lastrowid
		
		# Add card colours, rulings, types, and legality.
		
		# Colour:
		cardColours = cardData.get('colors',[])
		isWhite = int('White' in cardColours)
		isBlue  = int('Blue'  in cardColours)
		isBlack = int('Black' in cardColours)
		isRed   = int('Red'   in cardColours)
		isGreen = int('Green' in cardColours)
		isColourless = int(sum([isWhite,isBlue,isBlack,isRed,isGreen])==0)
		isMulti = int(sum([isWhite,isBlue,isBlack,isRed,isGreen])>=2)
		
		insertIntoTable('cardColours',(cardID,isWhite,isBlue,isBlack,isRed,isGreen,isColourless,isMulti))
		
		# Rulings:
		cardRulings = cardData.get('rulings',{})
		for ruling in cardRulings:
			insertIntoTable('cardRulings',(cardID,ruling['text'],ruling['date']))
			
		
		# Types:
		cardTypes = cardData.get('supertypes',[])+cardData.get('types',[])+cardData.get('subtypes',[])
		for cardType in cardTypes:
			insertIntoTable('cardTypes',(cardID,cardType))
		
		# Legality:
		cardLegalities = cardData.get('legalities',{})
		for legality in cardLegalities:
			insertIntoTable('cardLegality',(cardID,legality['format'],legality['legality']))
			
		# All card data has been added.

	elif len(result) == 1:
		cardID = result[0][0]
	else:
		print("####### POSSIBLE ERROR #######")
	
	# Now add the card edition stuff.
	
	
		
		
	
	# cardData we need to import:
	# 	cardName
	# 	cardManaCost
	# 	cardCMC
	# 	cardTypeLine
	# 	cardOracleText
	# 	cardLegendText
	# 	cardPower
	# 	cardToughness
	# 	cardLoyalty
	# 	cardHandMod
	# 	cardLifeMod
	# 	cardIsReserved
	# 	cardLayout
	# editionData we need to import:
	# 	editionRarity
	# 	editionFlavour
	# 	editionNumber
	# 	editionImage
	# 	editionArtist
	# 	editionWatermark
	# 	editionBorder
	# 	editionIsTimeshifted
	# 	editionReleaseDate
	# 	editionIsStarter
	# 	editionNotes
	# 	cardID
	# 	setID
			
def importSet(setCode):
	setFile = AllSets.get(setCode)
	if setFile:
		setName = setFile.get('name')
		setCode = setFile.get('code')
		setGathererCode = setFile.get('gathererCode',setCode)
		setOldCode = setFile.get('oldCode',setCode)
		setInfoCode = setFile.get('magicCardsInfoCode',None)
		setReleaseDate = setFile.get('releaseDate')
		setBorder = setFile.get('border')
		setType = setFile.get('type')
		setBlock = setFile.get('block',None)
		setIsOnlineOnly = setFile.get('onlineOnly',0)
		
		insertIntoTable('cardSets',(setName,setCode,setGathererCode,setOldCode,setInfoCode,setReleaseDate,setBorder,setType,setBlock,setIsOnlineOnly))
		
		cards = setFile.get('cards')
		for card in cards:
			# TODO: This
			#importCard(card)
			pass
		
importSet('LEA')
db.commit()