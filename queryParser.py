#!/usr/bin/python
#
# queryParser.py
#
# Takes a TreasuredFind query as input and outputs a SQLite3 statement.
#
# Created by Donald Sutherland on 7th November 2015

LIST_HELPER = lambda l: [i for i in l[:-1] if i!=""]+[l[-1]]

def queryParser(q):
	def queryHelper(level, singleQuoteMode, doubleQuoteMode):
		try:
			token = next(tokens)
		except StopIteration:
			if level != 0:
				raise Exception("Missing close character")
			else:
				return []
		if token == '"':
			if singleQuoteMode == True:
				return [token]+queryHelper(level, singleQuoteMode, doubleQuoteMode)
			elif doubleQuoteMode == False:
				doubleQuoteMode = True
				return [["|quote|", ""] + queryHelper(level+1, singleQuoteMode, doubleQuoteMode)] + queryHelper(level, singleQuoteMode, False)
			else:
				doubleQuoteMode = False
				return []
		elif token == "'":
			if doubleQuoteMode == True:
				return [token]+queryHelper(level, singleQuoteMode, doubleQuoteMode)
			elif singleQuoteMode == False:
				singleQuoteMode = True
				return [["|quote|", ""] + queryHelper(level+1, singleQuoteMode, doubleQuoteMode)] + queryHelper(level, False, doubleQuoteMode)
			else:
				singleQuoteMode = False
				return []
		elif token == ')':
			if singleQuoteMode == True or doubleQuoteMode == True:
				return [token]+queryHelper(level, singleQuoteMode, doubleQuoteMode)
			elif level == 0:
				raise Exception('Missing opening parenthesis')
			else:
				return []
		elif token == '(':
			if singleQuoteMode == True or doubleQuoteMode == True:
				return [token]+queryHelper(level, singleQuoteMode, doubleQuoteMode)
			else:
				return [["|bracket|", ""] + queryHelper(level+1, singleQuoteMode, doubleQuoteMode)] + queryHelper(level, singleQuoteMode, doubleQuoteMode)
		else:
			return [token] + queryHelper(level, singleQuoteMode, doubleQuoteMode)
	tokens = iter(q)
	return queryHelper(0,False,False)

def parserPretty(r):
	length = len(r)
	resultList = []
	resultString = ""
	for i in range(length):
		if isinstance(r[i], str):
			if r[i] == "|quote|" or r[i] == "|bracket|":
				resultList.append(r[i])
			else:
				resultString += r[i]
		elif isinstance(r[i], list):
			#if r[i][0] == "|quote|":
			#	if len(resultString) > 0 and resultString[-1] == " ":
			#		# This is a name query
			#		resultString += "name:"
			
			if resultString != "":
				resultList.append(resultString)
			resultString = ""
			resultList.append(parserPretty(r[i]))
	if resultString != "":
		resultList.append(resultString)
	return resultList

def parserPrettyPretty(x, ignoreStrings=False):
	resultList = []	
	for r in x:
		print(r)
		if isinstance(r, str): 
			if ignoreStrings == False:
				result = r.split(" ")
				resultList += LIST_HELPER(result)
			elif ignoreStrings == True:
				resultList += [r]
		
		if isinstance(r, list):
			if r[0] == "|quote|":
				if len(resultList) == 0 or resultList[-1] == "" or isinstance(resultList[-1], tuple):
					# Name query
					resultList += ["name:"+r[1]]
				elif isinstance(resultList[-1], str):
					# Append to the last arg
					resultList[-1] += r[1]
			elif r[0] == "|bracket|":
				resultList += [tuple(parserPrettyPretty(r[1:]))]
				
	return resultList


if __name__ == '__main__':
	while True:
		s = input("Query:  ")
		if s == "":
			break
		x = queryParser(s)
		y = parserPretty(x)
		z = parserPrettyPretty(y)
		print("Result:", z)
		print()