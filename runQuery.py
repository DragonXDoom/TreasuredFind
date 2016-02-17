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
				
				comparator = groups[0]
				colours = groups[1]
				#[cWhite, cBlue, cBlack, cRed, cGreen, cCLess, cMulti] = ['w' in colours, 'u' in colours, 'b' in colours, 'r' in colours, 'g' in colours, 'c' in colours, 'm' in colours]
				if matchtype == "colour":
					table = "cardColours"
				elif matchtype == "colourIden":
					table = "cardColourIdentity"
					
				isWhite = ('w' in colours)
				isBlue = ('u' in colours)
				isBlack = ('b' in colours)
				isRed = ('r' in colours)
				isGreen = ('g' in colours)
				isCLess = ('c' in colours)
				multi = ('m' in colours)
				
				if comparator == ":" and matchtype == "colour":
					statementPieces = []
					if isWhite:
						statementPieces.append("{0}.isWhite = 1".format(table))
					if isBlue:
						statementPieces.append("{0}.isBlue = 1".format(table))
					if isBlack:
						statementPieces.append("{0}.isBlack = 1".format(table))
					if isRed:
						statementPieces.append("{0}.isRed = 1".format(table))
					if isGreen:
						statementPieces.append("{0}.isGreen = 1".format(table))
					if isCLess:
						statementPieces.append("{0}.isColourless = 1".format(table))
					
					if len(statementPieces) > 0:
						statement = "("+(" OR ".join(statementPieces))+")"
					
					if multi:
						statement = "("+statement+" AND {0}.isMulti = 1)".format(table)
					
				elif comparator == "!" or matchtype == "colourIden":
					# Exclude unselected.
					statementPiecesTrue = []
					statementPiecesFalse = []
					
					
					if isWhite:
						statementPiecesTrue.append("{0}.isWhite = 1".format(table))
					else:
						statementPiecesFalse.append("{0}.isWhite = 0".format(table))
						
					if isBlue:
						statementPiecesTrue.append("{0}.isBlue = 1".format(table))
					else:
						statementPiecesFalse.append("{0}.isBlue = 0".format(table))
						
					if isBlack:
						statementPiecesTrue.append("{0}.isBlack = 1".format(table))
					else:
						statementPiecesFalse.append("{0}.isBlack = 0".format(table))
						
					if isRed:
						statementPiecesTrue.append("{0}.isRed = 1".format(table))
					else:
						statementPiecesFalse.append("{0}.isRed = 0".format(table))
						
					if isGreen:
						statementPiecesTrue.append("{0}.isGreen = 1".format(table))
					else:
						statementPiecesFalse.append("{0}.isGreen = 0".format(table))
						
						
					if matchtype != "colourIden":
						if isCLess:
							statementPiecesTrue.append("{0}.isColourless = 1".format(table))
						else:
							statementPiecesFalse.append("{0}.isColourless = 0".format(table))
						
						if multi == False:
							statement = "((" + " OR ".join(statementPiecesTrue) +") AND (" + " AND ".join(statementPiecesFalse) + "))"
						if multi == True:
							statement = "(" + " AND ".join(statementPiecesTrue) + " AND " + " AND ".join(statementPiecesFalse) + ")"
					else:
						if multi == False:
							statement = "(" + " AND ".join(statementPiecesFalse) + ")"
						if multi == True:
							statement = "((" + " AND ".join(statementPiecesFalse) + ") AND ( " + " OR ".join(statementPiecesTrue) + ") AND ({0}.isMulti = 1))".format(table)
					
			elif matchtype == "type":
				types = groups[0].split()
				# TODO
				
			return statement


if __name__ == '__main__':
	while True:
		x = input("> ")
		if not x: break
		else: print(convertToSQL(x))