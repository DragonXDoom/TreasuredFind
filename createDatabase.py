#!/usr/bin/python
#
# createDatabase.py
#
# Creates the internal database required for TreasuredFind
#
# Created by Donald Sutherland on 7th November 2015

import sqlite3 as sql

DATABASE_NAME = 'cardDB.sqlite3'
TABLE_NAMES = ['cardData','cardSets','cardEditions']

db = sql.connect(DATABASE_NAME)
curs = db.cursor()

for table in TABLE_NAMES:
	curs.execute("DROP TABLE IF EXISTS %s" % table)

curs.execute("""
		CREATE TABLE IF NOT EXISTS cardData (
			 cardID 				INTEGER PRIMARY KEY AUTOINCREMENT,
			 cardName 				TEXT NOT NULL,
			 cardManaCost 			TEXT,
			 cardCMC 				REAL NOT NULL,
			 cardTypeLine 			TEXT,
			 cardOracleText 		TEXT,
			 cardPower 				REAL,
			 cardToughness 			REAL,
			 cardLoyalty 			REAL,
			 cardHandMod 			REAL,
			 cardLifeMod 			REAL,
			 cardIsReserved 		INTEGER NOT NULL,
			 cardLayout 			TEXT
		)
			 """)

curs.execute("""
		CREATE TABLE IF NOT EXISTS cardSets (
			setID					INTEGER PRIMARY KEY AUTOINCREMENT,
			setName					TEXT NOT NULL,
			setCode					TEXT NOT NULL,
			setGathererCode			TEXT NOT NULL,
			setOldCode				TEXT NOT NULL,
			setInfoCode				TEXT,
			setReleaseDate			TEXT NOT NULL,
			setBorder				TEXT NOT NULL,
			setType					TEXT NOT NULL,
			setBlock				TEXT,
			setIsOnlineOnly			INTEGER NOT NULL
		);
			 """)

curs.execute("""
		CREATE TABLE IF NOT EXISTS cardEditions (
			editionID 				INTEGER PRIMARY KEY AUTOINCREMENT,
			editionRarity			TEXT NOT NULL,
			editionFlavour			TEXT,
			editionNumber			TEXT NOT NULL,
			editionImage			TEXT NOT NULL,
			editionWatermark		TEXT,
			editionBorder			TEXT NOT NULL,
			editionIsTimeshifted	INTEGER NOT NULL,
			editionReleaseDate		TEXT NOT NULL,
			editionIsStarter		INTEGER NOT NULL,
			editionNotes			TEXT,
			cardID					INTEGER NOT NULL,
			setID					INTEGER NOT NULL,
			FOREIGN KEY(cardID) REFERENCES cardData(cardID),
			FOREIGN KEY(setID) REFERENCES cardSets(setID)
		);
			""")