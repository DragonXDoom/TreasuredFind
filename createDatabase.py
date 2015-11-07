#!/usr/bin/python
#
# createDatabase.py
#
# Creates the internal database required for TreasuredFind
#
# Created by Donald Sutherland on 7th November 2015

import sqlite3 as sql

DATABASE_NAME = 'cardDB.sqlite3'

db = sql.connect(DATABASE_NAME)
curs = db.cursor()

curs.execute("""CREATE TABLE IF NOT EXISTS cardData (
			 cardID INTEGER PRIMARY KEY AUTOINCREMENT,
			 cardName TEXT NOT NULL,
			 cardManaCost TEXT,
			 cardCMC REAL NOT NULL,
			 cardTypeLine TEXT,
			 cardOracleText TEXT,
			 cardPower REAL,
			 cardToughness REAL,
			 cardLoyalty REAL,
			 cardHandMod REAL,
			 cardLifeMod REAL,
			 cardIsReserved INTEGER NOT NULL,
			 cardLayout TEXT)
			 WITHOUT ROWID""")