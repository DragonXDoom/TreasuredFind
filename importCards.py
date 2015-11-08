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
TRUE_FALSE_MAP = {'true':1,'false':0}

otherPartsNames = {}

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
		
def insertIntoTable(tableName, values, includeRowId=False):
	curs.execute("PRAGMA table_info({})".format(tableName))
	columnNames = curs.fetchall()
	if not includeRowId:
		columnNames = columnNames[1:]
	columnNames = list(map(lambda x: x[1], columnNames))
	#print(columnNames)
	statement = "INSERT INTO {table}({columns}) VALUES ({params})".format(table=tableName,columns=','.join(columnNames),params=','.join(["?" for i in range(len(columnNames))]))
	#print(statement)
	curs.execute(statement,values)

def importCard(cardData, setID, setBorder, setReleaseDate):
	# Check if card exists already.
	# If so, just add edition
	# Otherwise add both card data and card edition data.
	
	global otherPartsNames
	
	cardName = cardData.get('name')
	curs.execute("SELECT cardID FROM cardData WHERE cardName = ?",(cardName,))
	result = curs.fetchall()
	if len(result) == 0: # If the card isn't in the card database...
		cardManaCost = cardData.get('manaCost')
		cardCMC = cardData.get('cmc',0)
		cardTypeLine = cardData.get('type')
		cardOracleText = cardData.get('text',"")
		
		cardPower = cardData.get('power')
		cardToughness = cardData.get('toughness')
		cardLoyalty = cardData.get('loyalty')
		cardHandMod = cardData.get('hand')
		cardLifeMod = cardData.get('life')
		cardIsReserved = int(cardData.get('reserved',0))
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
		
		insertIntoTable('cardColours',(cardID,isWhite,isBlue,isBlack,isRed,isGreen,isColourless,isMulti),True)
		
		# Rulings:
		cardRulings = cardData.get('rulings',{})
		for ruling in cardRulings:
			insertIntoTable('cardRulings',(cardID,ruling['text'],ruling['date']),True)
			
		
		# Types:
		cardTypes = cardData.get('supertypes',[])+cardData.get('types',[])+cardData.get('subtypes',[])
		for cardType in cardTypes:
			insertIntoTable('cardTypes',(cardID,cardType),True)
		
		# Legality:
		cardLegalities = cardData.get('legalities',{})
		for legality in cardLegalities:
			insertIntoTable('cardLegality',(cardID,legality['format'],legality['legality']),True)
			
		# All card data has been added.

	elif len(result) == 1:
		cardID = result[0][0]
	else:
		print("####### POSSIBLE ERROR #######")
	
	# Now add the card edition stuff.
	
	editionRarity = cardData.get('rarity')
	editionFlavour= cardData.get('flavor',"")
	editionNumber = cardData.get('number',"")
	editionImage  = cardData.get('imageName',"")
	editionArtist = cardData.get('artist',"")
	edtionWatermark=cardData.get('watermark',"")
	editionBorder = cardData.get('border',setBorder)
	editionTimeShifted = int(cardData.get('timeshifted',0))
	editionReleaseDate = cardData.get('releaseDate', setReleaseDate)
	editionIsStarter = int(cardData.get('starter',0))
	editionNotes = cardData.get('source')
	
	insertIntoTable('cardEditions',(editionRarity,editionFlavour,editionNumber,editionImage,editionArtist,edtionWatermark,editionBorder,editionTimeShifted,editionReleaseDate,editionIsStarter,editionNotes,cardID,setID))
	
	editionID = curs.lastrowid
	
	# Check for other parts
	names = cardData.get('names')
	if names != None:
		names.remove(cardName)
		otherPartsNames[cardName] = [editionID]+[names]
	
	print("Successfully imported {}".format(cardName))
			
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
		
		setID = curs.lastrowid
		
		cards = setFile.get('cards')
		for card in cards:
			importCard(card, setID, setBorder, setReleaseDate)
			
		global otherPartsNames
		for key in otherPartsNames:
			names = list(otherPartsNames[key])
			currentID = names.pop(0)
			otherIDs = list(map(lambda s:otherPartsNames[s][0]))
			for otherID in otherIDs:
				insertIntoTable('otherParts',(currentID, otherID),True)
		
		

if __name__ == '__main__':
	for setCode in ["LEA","LEB","ARN","2ED","CED","CEI","pDRC","ATQ","3ED","LEG","DRK","pMEI","FEM","pLGM","4ED","ICE","CHR","HML","ALL","RQS","pARL","pCEL","MIR","MGB","ITP","VIS","5ED","pPOD","POR","VAN","WTH","pPRE","TMP","STH","PO2","pJGP","EXO","UGL","pALP","USG","ATH","ULG","6ED","PTK","UDS","S99","pGRU","pWOR","pWOS","MMQ","BRB","pSUS","pFNM","pELP","NMS","S00","PCY","BTD","INV","PLS","7ED","pMPR","APC","ODY","DKM","TOR","JUD","ONS","LGN","SCG","pREL","8ED","MRD","DST","5DN","CHK","UNH","BOK","SOK","9ED","RAV","p2HG","pGTW","GPT","pCMP","DIS","CSP","CST","TSP","TSB","pHHO","PLC","pPRO","pGPX","FUT","10E","pMGD","MED","LRW","EVG","pLPA","MOR","p15A","SHM","pSUM","EVE","DRB","ME2","pWPN","ALA","DD2","CON","DDC","ARB","M10","V09","HOP","ME3","ZEN","DDD","H09","WWK","DDE","ROE","DPA","ARC","M11","V10","DDF","SOM","PD2","ME4","MBS","DDG","NPH","CMD","M12","V11","DDH","ISD","PD3","DKA","DDI","AVR","PC2","M13","V12","DDJ","RTR","CM1","GTC","DDK","pWCQ","DGM","MMA","M14","V13","DDL","THS","C13","BNG","DDM","JOU","MD1","CNS","VMA","M15","CPK","V14","DDN","KTK","C14","DD3_DVD","DD3_EVG","DD3_GVL","DD3_JVC","FRF_UGIN","FRF","DDO","DTK","TPR","MM2","ORI","V15","DDP","BFZ","EXP"]:
		importSet(setCode)
		db.commit()
	db.commit()