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
			importCard(card)
		
importSet('LEA')
db.commit()