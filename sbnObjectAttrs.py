import maya.cmds as cmds

class itemAndRow(object):
	def __init__(self):
		self.row = None 
		self.uni = ''	# Unicode
		self.item = ''	# Hexa code

class undoObject(object):
	def __init__(self):
		self.row = []
		self.objects = []
		self.correspondsTo = None
		self.next = []
		self.lastItem = ''
		self.lastKey = ''
		self.possibleLenght = 0

class UIInfos(object):
	def __init__(self):
		self.userEnabledAbsoluteUpdating = False # User choice, update or not the script while doing huge selections.
		self.isFocused = False # Check if the window or its childrens has focus
		self.advancedFilteringIsEnabled = False #User choice
		self.allowShapes = False # Allow shape nodes or not.
		self.userAllowsShapes = False # User choice, allow shape nodes or not.
		self.objectError = False # If the script finds errors (non-existant nodes, for example)
		self.allowAbsEverythin = False # User choice, allow system nodes, or not.
		self.selectShiftJumpEnabled = False # Check if Shift is pressed in the list widget.
		self.persistentEditorOpen = False # Check if sbn is in renaming mode.
		self.resetIfEnabled = False # Reset the UI after a selection modification and a select All (CTRL+A) 
		self.enableUpdating = True # Has priority by default
		self.enabledAbsoluteUpdating = False
		self.userDisabledKeyEventForQlist = False # Set to False, the user can't use letters as shortcuts for the word starting with what is pressed, but he can do a lot of other stuff.
		self.userEnabledUpdating = True # Has priority if set to False
		self.ignoreCapital = False
		self.wasUpdatedAfterFocus = False
		self.nothingLeftToUndo = True
		self.hasBeenSaid = False
		self.currentNumberOfObjects = 0
			
class rebuiltList(object):
	def __init__(self):
		self.item = []
		self.index = []



def getCurrentScene():
	scene = cmds.file(q=1, sn=1)
	if scene == '':
		return 'temp'
	else:
		cp = 0
		p = 0
		while True:
			p = scene.find('/', cp)
			if p == -1:
				ex = scene.find('.', cp)
				return scene[cp:ex]

			cp = p+1

def checkStrSyntax(string):
	formatter1 = string.find('{')
	formatter2 = string.find('}')
	if formatter1 == formatter2: return False

	if formatter1+1 == formatter2 and not string.isdigit(): return False
	else: return True

def removeSpacing(item, accept, removeWhat): # This function does NOT work for random applications. It's only for linear names. 
	row = 0
	spacing = False
	remove = set(removeWhat)
	for string in item:
		if string in remove:
			item = item.replace(string, '')
			row += 1
			spacing = True
		elif string in accept:
			break
	row += 1
	return item, spacing, row # Return newName

def nbrOfTimesItAppears(item, what): #Recursive function FTW!
	qt = 1
	while what in item:
		item = str(item.replace(what, '', 1))
		qt += 1

	return item, qt # Return item's new name, and the number of time "what" string appears in the item	

def querySC(SC):
	thereIsSomething = False
	ignore = False
	presetsMode = False
	what = []
	whatNot = []
	rank = 0
	for i in SC:
		if i.text() != '':
			thereIsSomething = True
			what.append(rank)
		else:
			whatNot.append(rank)
		rank += 1
		if i.text() == '@all':
			ignore = True
		elif i.text() == '@pre':
			presetsMode = True	
				
	return thereIsSomething, what, whatNot, ignore, presetsMode # Return if there is something, what is filled with something, what isn't and if "@all" or "@pre" was typed	


def rebuildSelectionOrder(items):
	"""
	This function makes a proper selection for Maya. Useful when using tools that need a selection order.
	"""
	selectionDic = {}
	order = [i.selectionOrder() for i in items]

	for x, obj in zip(order, items):
		selectionDic["O%d"%x] = obj

	order.sort()
	output = []
	for i in order:
		output.append(selectionDic["O%d"%i])

	return output

