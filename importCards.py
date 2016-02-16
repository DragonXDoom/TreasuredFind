#!/usr/bin/python
#
# importCards.py
#
# Adds all cardData from a JSON file into the database.
# This JSON file should follow the formatting supplied by http://mtgjson.com
# The database is created by createDatabase.py
#
# Created by Donald Sutherland on 7th November 2015

import sqlite3 as sql
import json
import urllib.request, urllib.parse, urllib.error
import re
from distutils.version import StrictVersion 

ALL_SETS_URL = 'http://mtgjson.com/json/AllSets-x.json'
VERSION_URL  = 'http://mtgjson.com/json/version.json'
DATABASE_NAME = 'cardDB.sqlite3'
MANA_SYMBOLS = ['{W}', '{U}', '{B}', '{R}', '{G}', '{C}'
				'{W/U}', '{R/W}', '{W/B}', '{B/R}', '{G/U}', '{G/W}', '{U/R}', '{R/G}', '{B/G}', '{U/B}',
				'{2/W}', '{2/U}', '{2/B}', '{2/R}', '{2/G}',
				'{WP}', '{UP}', '{BP}', '{RP}', '{GP}']
COLOURS = ['W','U','B','R','G']
REMINDER_TEXT_PATTERN = re.compile(r"\(.*?\)")
LEGEND_NAME_PATTERN = re.compile(r"^([^,\s]+).*$")
TUPLE_MERGER = lambda x,y: x|y

otherPartsNames = {}

db = sql.connect(DATABASE_NAME)
curs = db.cursor()


def updateInformation():
	print("\nChecking for updated version...")
	with open("version.json","r") as versionFile:
		version = versionFile.read()
		print("Current Version:",version)
	try:
		urllib.request.urlretrieve(VERSION_URL, "version.json")
		with open("version.json","r") as versionFile:
			newVersion = versionFile.read()
			print("Latest Version:",newVersion)
		if StrictVersion(newVersion.strip('"'))>StrictVersion(version.strip('"')):
			print("Downloading MTGJSON version",newVersion)
			updateAllSets()
	except urllib.error.URLError:
		print("Unable to check new version.")
	

def updateAllSets():
	urllib.request.urlretrieve(ALL_SETS_URL, "AllSets-x.json")
	
#updateInformation()
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
		if cardTypeLine.startswith("Legendary") or cardTypeLine.startswith("Planeswalker"):
			match = LEGEND_NAME_PATTERN.match(cardName)
			if match:
				print(match.group(1))
				cardLegendText = cardLegendText.replace(match.group(1), "~")
		
		cardLegendText = REMINDER_TEXT_PATTERN.sub("", cardLegendText)
		
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
		
		# Colour Identity:
		cardColoursIden = cardData.get('colorIdentity',[])
		idenIsWhite = int('W' in cardColoursIden)
		idenIsBlue  = int('U' in cardColoursIden)
		idenIsBlack = int('B' in cardColoursIden)
		idenIsRed   = int('R' in cardColoursIden)
		idenIsGreen = int('G' in cardColoursIden)
		idenIsColourless = int(sum([idenIsWhite,idenIsBlue,idenIsBlack,idenIsRed,idenIsGreen])==0)
		idenIsMulti = int(sum([idenIsWhite,idenIsBlue,idenIsBlack,idenIsRed,idenIsGreen])>=2)
		
		insertIntoTable('cardColours',(cardID,isWhite,isBlue,isBlack,isRed,isGreen,isColourless,isMulti),True)
		insertIntoTable('cardColourIdentity',(cardID,idenIsWhite,idenIsBlue,idenIsBlack,idenIsRed,idenIsGreen,idenIsColourless,idenIsMulti),True)
		
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
	
	insertIntoTable('cardEditions',(editionRarity,editionFlavour,editionNumber,editionImage,editionArtist,edtionWatermark,editionBorder,editionTimeShifted,editionReleaseDate,editionIsStarter,editionNotes,1,cardID,setID))
	
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
		print(otherPartsNames)
		# {'Death': [1616, ['Life']], 'Ice': [1663, ['Fire']], 'Life': [1677, ['Death']], 'Fire': [1640, ['Ice']]}
		for key in otherPartsNames:
			names = list(otherPartsNames[key])
			currentID = names.pop(0)
			otherIDs = list(map(lambda s:otherPartsNames[s][0], names[0]))
			for otherID in otherIDs:
				insertIntoTable('otherParts',(currentID, otherID),True)
		otherPartsNames = {}
				
def checkForReprints():
	print("CHECKING FOR REPRINTS")
	statement = """
	UPDATE cardEditions
	SET editionIsReprint = 0
	WHERE editionID IN (
		SELECT editionID
		FROM cardEditions
		WHERE editionReleaseDate = (
			SELECT MIN(editionReleaseDate)
			FROM cardEditions
			WHERE cardID = ?
			)
		AND cardID = ?
	)
	"""
	curs.execute("SELECT cardID FROM cardData")
	ids = list(map(lambda s:s[0], curs.fetchall()))
	for ID in ids:
		curs.execute(statement,(ID,ID))
	db.commit()
		
def checkForOtherPart(cardID):
	statement = """SELECT cardData.cardID FROM cardData INNER JOIN cardEditions
	WHERE cardEditions.editionID IN (SELECT otherParts.otherPartID FROM cardData INNER JOIN cardEditions INNER JOIN otherParts
	WHERE cardData.cardID = ? AND cardEditions.cardID = cardData.cardID AND cardEditions.editionID = otherParts.editionID) AND cardEditions.cardID = cardData.cardID"""
	curs.execute(statement, (cardID,))
	return curs.fetchall()

def checkColourIdentity(cardID):
	# Obsolete as of MtGJSON version 3.3.6
	curs.execute("SELECT cardData.cardManaCost, cardData.cardLegendText,cardColours.isWhite,cardColours.isBlue,cardColours.isBlack,cardColours.isRed,cardColours.isGreen FROM cardData INNER JOIN cardColours WHERE cardColours.cardID = cardData.cardID AND cardData.cardID = ?", (cardID,))
	data = curs.fetchone()
	manaCost = data[0]
	if manaCost == None: manaCost = ""
	legendText = data[1]
	if legendText == None: legendText = ""
	colours = data[2:]
	symbols = ""
	result = [0,0,0,0,0]
	for symbol in MANA_SYMBOLS:
		if symbol in manaCost or symbol in legendText:
			symbols += symbol
	for i in range(5):
		if COLOURS[i] in symbols:
			result[i] = 1
	result = list(map(TUPLE_MERGER,result,colours))
	#result += [int(sum(result)==0),int(sum(result))>=2]
	return tuple(result)
	

def updateColourIdentity():
	# Obsolete as of MtGJSON version 3.3.6
	curs.execute("SELECT cardID FROM cardData")
	ids = list(map(lambda s:s[0], curs.fetchall()))
	for ID in ids:
		identity = (0,0,0,0,0)
		result = checkForOtherPart(ID)
		if result != []:
			result = list(map(lambda i:i[0], result))
			for otherPartID in result:
				identity = tuple(map(TUPLE_MERGER, identity, checkColourIdentity(otherPartID)))
		identity = tuple(map(TUPLE_MERGER, identity, checkColourIdentity(ID)))
		identity = (ID,) + identity + (int(sum(identity)==0),int(sum(identity))>=2)
		insertIntoTable("cardColourIdentity", identity, True)
		print("Succesfully updated colour identity for cardID", ID)
	db.commit()
		
if __name__ == '__main__':
	for setCode in AllSets:
		importSet(setCode)
		db.commit()
	checkForReprints()
	#updateColourIdentity()
	db.commit()
