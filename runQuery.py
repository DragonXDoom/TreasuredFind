#!/usr/bin/python
#
#
#
#

import re
import sqlite3


namePattern = re.compile(r"name:(.*)")
oraclePattern = re.compile(r"o:(.*)")
cmcPattern = re.compile(r"cmc([<>=]{1,2})(.+)")
powerPattern = re.compile(r"pow([<>=]{1,2})(.+)")
toughnessPattern = re.compile(r"tou([<>=]{1,2})(.+)")
coloursPattern = re.compile(r"c([!:])([wubrgmc]+)")
colourIdentityPattern = re.compile(r"ci([!:])([wubrgmc]+)")
typesPattern = re.compile(r"t:(.+)")

special_comparisons = {
	"pow": "cardData.cardPower",
	"tou": "cardData.cardToughness",
	"cmc": "cardData.cardCMC"
}

patterns = {
	namePattern: "name",
	oraclePattern: "oracle",
	cmcPattern: "cmc",
	powerPattern: "power",
	toughnessPattern: "toughness",
	coloursPattern: "colour",
	colourIdentityPattern: "colourIden",
	typesPattern: "type"
}

BASE_STATEMENT = """
SELECT cardEditions.editionID
FROM
	cardData
	INNER JOIN cardEditions ON cardData.cardID = cardEditions.cardID
	INNER JOIN cardColours ON cardData.cardID = cardColours.cardID
	INNER JOIN cardColourIdentity ON cardData.cardID = cardColourIdentity.cardID
	INNER JOIN cardLegality ON cardData.cardID = cardLegality.cardID
	INNER JOIN cardTypes ON cardData.cardID = cardTypes.cardID
	INNER JOIN cardSets ON cardEditions.setID = cardSets.setID
WHERE
	cardData.cardName = ?
"""

SECOND_BASE_STATEMENT = """
SELECT cardEditions.editionID
FROM
	cardData
	INNER JOIN cardEditions ON cardData.cardID = cardEditions.cardID
	INNER JOIN cardColours ON cardData.cardID = cardColours.cardID
	INNER JOIN cardColourIdentity ON cardData.cardID = cardColourIdentity.cardID
	INNER JOIN cardLegality ON cardData.cardID = cardLegality.cardID
	INNER JOIN cardTypes ON cardData.cardID = cardTypes.cardID
	INNER JOIN cardSets ON cardEditions.setID = cardSets.setID
WHERE
	cardData.cardName = ?
GROUP BY
	cardData.cardID

"""

def convertToSQL(token):
	token = token.lower()
	statement = ""
	for pattern in patterns:
		match = pattern.match(token)
		if match:
			if token.startswith("-"):
				statement += "NOT "
			matchtype = patterns[pattern]
			groups = match.groups()
			if matchtype == "name":
				name = groups[0]
				statement = 'cardData.cardName LIKE "%{0}%"'.format(name)
			
			elif matchtype == "oracle":
				oracleText = groups[0]
				statement = 'cardData.cardLegendText LIKE "%{0}%"'.format(oracleText)
				
			elif matchtype == "cmc":
				comparator = groups[0]
				comparison = groups[1]
				comparison = special_comparisons.get(comparison,comparison) # If it's special, get the proper value. Otherwise leave it.
				if comparator in ["=","<",">","<=",">="]: # There aren't really any other comparators
					statement = "cardData.cardCMC {0} {1}".format(comparator, comparison)
					
			elif matchtype == "power":
				comparator = groups[0]
				comparison = groups[1]
				comparison = special_comparisons.get(comparison,comparison) # If it's special, get the proper value. Otherwise leave it.
				if comparator in ["=","<",">","<=",">="]: # There aren't really any other comparators
					statement = "cardData.cardPower {0} {1}".format(comparator, comparison)
					
			elif matchtype == "toughness":
				comparator = groups[0]
				comparison = groups[1]
				comparison = special_comparisons.get(comparison,comparison) # If it's special, get the proper value. Otherwise leave it.
				if comparator in ["=","<",">","<=",">="]: # There aren't really any other comparators
					statement = "cardData.cardToughness {0} {1}".format(comparator, comparison)
					
			elif matchtype == "colour" or matchtype == "colourIden":
				# WUBRG, C, M. ! means exclude unselected.
				statementPieces = []
				comparator = groups[0]
				colours = groups[1]
				#[cWhite, cBlue, cBlack, cRed, cGreen, cCLess, cMulti] = ['w' in colours, 'u' in colours, 'b' in colours, 'r' in colours, 'g' in colours, 'c' in colours, 'm' in colours]
				if matchtype == "colour":
					table = "cardColours"
				elif matchtype == "colourIden":
					table = "cardColourIdentity"
					
				multi = ('m' in colours)
				
				
				if comparator == ":":
					if 'w' in colours:
						statementPieces.append("{0}.isWhite = 1".format(table))
					if 'u' in colours:
						statementPieces.append("{0}.isBlue = 1".format(table))
					if 'b' in colours:
						statementPieces.append("{0}.isBlack = 1".format(table))
					if 'r' in colours:
						statementPieces.append("{0}.isRed = 1".format(table))
					if 'g' in colours:
						statementPieces.append("{0}.isGreen = 1".format(table))
					if 'c' in colours:
						statementPieces.append("{0}.isColourless = 1".format(table))
					
					if len(statementPieces) > 0:
						statement = "("+(" OR ".join(statementPieces))+")"
					
					if multi:
						statement = "("+statement+" AND {0}.isMulti = 1)".format(table)
					
				elif comparator == "!":
					# Exclude unselected.
					statementPiecesTrue = []
					statementPiecesFalse = []
					
					
					if 'w' in colours:
						statementPiecesTrue.append("{0}.isWhite = 1".format(table))
					else:
						statementPiecesFalse.append("{0}.isWhite = 0".format(table))
						
					if 'u' in colours:
						statementPiecesTrue.append("{0}.isBlue = 1".format(table))
					else:
						statementPiecesFalse.append("{0}.isBlue = 0".format(table))
						
					if 'b' in colours:
						statementPiecesTrue.append("{0}.isBlack = 1".format(table))
					else:
						statementPiecesFalse.append("{0}.isBlack = 0".format(table))
						
					if 'r' in colours:
						statementPiecesTrue.append("{0}.isRed = 1".format(table))
					else:
						statementPiecesFalse.append("{0}.isRed = 0".format(table))
						
					if 'g' in colours:
						statementPiecesTrue.append("{0}.isGreen = 1".format(table))
					else:
						statementPiecesFalse.append("{0}.isGreen = 0".format(table))
						
					if 'c' in colours:
						statementPiecesTrue.append("{0}.isColourless = 1".format(table))
					else:
						statementPiecesFalse.append("{0}.isColourless = 0".format(table))
						
					if multi == False:
						statement = "((" + " OR ".join(statementPiecesTrue) +") AND (" + " AND ".join(statementPiecesFalse) + "))"
					if multi == True:
						statement = "(" + " AND ".join(statementPiecesTrue) + " AND " + " AND ".join(statementPiecesFalse) + ")"
						
						
					
				
			elif matchtype == "colourIden":
				comparator = groups[0]
				colours = groups[1]
				# TODO
			elif matchtype == "type":
				types = groups[0].split()
				# TODO
				
			return statement
