import sbnSys

def open():
	global SBN_UI
	reload(sbnSys)
	try:
		SBN_UI.close()
	except:
		pass

	SBN_UI = sbnSys.SbnWidget()

def close():
	global SBN_UI
	try:
		SBN_UI.close()
		SBN_UI = None
	except:
		Warning("Window already closed")

def query():
	global SBN_UI
	if SBN_UI:
		return SBN_UI
	else:
		Warning("Window isn't active.")



