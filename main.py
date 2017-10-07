# TODO: redo scraping info that uses substring so it isn't as ugly

import re
import requests
from robobrowser import RoboBrowser

#temporary for debugging
from pprint import pprint

baseURL = 'https://dashboard.okaloosaschools.com'
loginURL = '/parentportal/PP000.pgm'

loginCred = {
	'wrkuser'  : '',
	'wrkpasswd': ''
}

studentInfo = {
	'birthdate': '',
	'gender'   : '',
	'race'     : '',

	'school'  : '',
	'grade'   : '',
	'date'    : '',
	'homeroom': '',

	'gpa-weight'  : '',
	'gpa-noweight': ''
}

schedule = {
	'semester1': {
		'classes' : [],
		'periods' : [],
		'teachers': [],
		'quarter1': [],
		'quarter2': [],
		'exams'   : [],
		'total'   : [],
		'final'   : []
	},

	'semester2' : {
		'classes' : [],
		'periods' : [],
		'teachers': [],
		'quarter1': [],
		'quarter2': [],
		'exams'   : [],
		'total'   : [],
		'final'   : []
	}
}

headers = {
	'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'
}
''' 
Info:

classes
	category summary
		category
		weight
		percent
	category
		assignment
			due date
			recevied
			max
			weight
			grade
			note
'''
classes = {
	'category_summary': [
		
	],

	'category': [
	]
}

def siteUp(site):
	try: 
		request = requests.get(site, headers=headers, timeout=5)
	except requests.ConnectionError as e:
		print("Oops! Connection Error. Make sure you are connected to Internet. Technical Details given below.\n")
		print(str(e))
		return False
	except requests.Timeout as e:
		print("OOPS!! Timeout Error")
		print(str(e))
		return False
	except requests.RequestException as e:
		print("OOPS!! General Error")
		print(str(e))
		return False
	except KeyboardInterrupt:
		print("Someone closed the program")
		return False
		
	return request.status_code == 200

def readConfig():
	### Read Credential File ###
	configFile = open(".config", "r")
	for line in configFile.readlines():
		splitted = line.split(":")

		if splitted[0] == "wrkuser":
			loginCred["wrkuser"] = splitted[1].replace('\n', '')
		elif splitted[0] == "wrkpasswd":
			loginCred["wrkpasswd"] = splitted[1].replace('\n', '')

	configFile.close()

def main():

	### Init ###
	browser = RoboBrowser(history=True, parser="html.parser")

	### Login ###
	browser.open(baseURL + loginURL)
	loginForm = browser.get_form(enctype=re.compile(r'multipart/form-data'))

	loginForm['wrkuser'].value = loginCred['wrkuser']
	loginForm['wrkpasswd'].value = loginCred['wrkpasswd']


	browser.submit_form(loginForm)

	### Redirect ###

	body = browser.select('body')
	redirectURL = body[0].get('onload')

	redirectURL = redirectURL[18:-3]

	browser.open(baseURL + redirectURL)

	### Logged In ###
	# print(browser.parsed)

	# debugfile = open("debug.html", "w")
	# debugfile.write(str(browser.parsed))
	# debugfile.close()

	### Student Info ###
	sideBar = browser.find_all("table", class_="classarea")[0].find_all("td")

	studentInfo['birthdate'] = str(sideBar[1]).replace('<td align="left"><u><b>Birthdate</b></u>: ', "")[:5]#[42:47]
	studentInfo['gender'] = str(sideBar[1])[71:-5]
	studentInfo['race'] = str(sideBar[2])[47:].replace('</td>', "")
	studentInfo['school'] = str(sideBar[4])[39:].replace('</td>', '').strip()
	studentInfo['grade'] = str(sideBar[5])[38:-37]
	studentInfo['date'] = str(sideBar[5])[-14:-5]
	studentInfo['homeroom'] = str(sideBar[7])[41:-5]
	studentInfo['gpa-weight'] = str(sideBar[9])[41:47]
	studentInfo['gpa-noweight'] = str(sideBar[9])[75:81]

	### Grade Stuff ###
	tableSections = browser.find_all("table", class_="classarea")
	
	gradePosition = 3
	if len(tableSections) == 8:
		gradePosition = 4
	gradeSection = tableSections[gradePosition].find_all("tr")
	print(len(tableSections))
	#print(tableSections)
	gradeSection = gradeSection[2:-1]

	counter = 2

	### Teacher/Class Info ###
	for sec in gradeSection:
		#print(sec.find_all("td"))
		for className in sec.find_all("td"):
			if 'title' in className.attrs:
				if counter % 2 == 0:
					schedule['semester1']['classes'].append(className.attrs['title'])
				else:
					schedule['semester1']['teachers'].append(className.attrs['title'])

				counter += 1

	### Period Info ###
	for sec in gradeSection:
		for period in sec.find_all('td', { "title": "", "align": "" }):
			schedule['semester1']['periods'].append(period.text)

	### Grade Info ###
	for sec in gradeSection:
		for i, boop in enumerate(sec.find_all('td', { "align": "right" })):
			if(i + 5 % 5 == 0):
				schedule['semester1']['quarter1'].append(boop.findChildren()[0].text)
				#print(boop.findChildren()[0].text)
			if(i + 5 % 5 == 1):
				schedule['semester1']['quarter2'].append(boop.findChildren()[0].text)
			if(i + 5 % 5 == 2):
				schedule['semester1']['exams'].append(boop.text)
			if(i + 5 % 5 == 3):
				schedule['semester1']['total'].append(boop.text)
			if(i + 5 % 5 == 4):
				schedule['semester1']['final'].append(boop.text)

	### Class Grade Info ###
	#apparently wrkgrpd=1 is 1st quarter and wrkgrpd=2 is 2nd quarter. This needs to best tested with others quarters
	SMURFID = redirectURL[32:64]

	grPdReqUrlStart = "https://dashboard.okaloosaschools.com/parentportal/DP400.pgm?task=setgrpd&SmurfId="
	grPdReqUrlEnd = "&timestamp=&wrkgrpd=1"

	grPdReqUrl = grPdReqUrlStart + SMURFID + grPdReqUrlEnd
	# print(grPdReqUrl)

	schlReqStart = "https://dashboard.okaloosaschools.com/parentportal/DP400.pgm?task=setschl&SmurfId="
	schlReqEnd = "&timestamp=&wrkschl=0211"

	schlReqUrl = schlReqStart + SMURFID + schlReqEnd
	# print(schlReqUrl)

	for count, sec in enumerate(gradeSection):
		for i, boop in enumerate(sec.find_all('td', { "align": "right" })):
			if(i + 5 % 5 == 0):
				# browser.follow_link(boop.findChildren()[0])
				linkHrefStuff = boop.findChildren()[0]['href']
				linkProcStuff = linkHrefStuff[80:-2].replace("'", '')
				linkProcSplit = linkProcStuff.split(",")

				# Clean up list
				linkProcSplit[:] = [s.replace('\n\t', '') for s in linkProcSplit]
				linkProcSplit[:] = [s.replace(' ', '') for s in linkProcSplit]
				#print(linkProcSplit)

				linkProcUrl = "https://dashboard.okaloosaschools.com/parentportal/DP900.pgm?task=lnkproc&SmurfId=" + linkProcSplit[1]
				linkProcUrl += "&timestamp=&from_menu=" + linkProcSplit[2]
				linkProcUrl += "&to_menu=" + linkProcSplit[3]
				linkProcUrl += "&from_pgm=" + linkProcSplit[4]
				linkProcUrl += "&to_pgm=" + linkProcSplit[5]
				linkProcUrl += "&wrkstaf=" + linkProcSplit[6]
				linkProcUrl += "&wrkcrse=" + linkProcSplit[7]
				linkProcUrl += "&wrksect=" + linkProcSplit[8]
				linkProcUrl += "&wrkstdt=" + linkProcSplit[9]
				
				# print(grPdReqUrl)
				# print('\n')
				# print(schlReqUrl)
				# print('\n')
				# print(linkProcUrl)
				# print("-" * 10)

				browser.session.get(grPdReqUrl)
				browser.session.get(schlReqUrl)
				browser.session.get(linkProcUrl)
				
				browser.open('https://dashboard.okaloosaschools.com/parentportal/PP200.pgm?SMURFID=' + SMURFID + "&rand=")
				#print(browser.parsed)
				
				# Debugging
				# debugfile = open("debug" + str(count) +".html", "a")
				# debugfile.truncate()
				# debugfile.write(str(browser.parsed))
				# debugfile.close()

				# Parse information
				categories = browser.find_all("table", class_="classarea")[1:]

				# Category Summary
				summaryCat = categories[-1].find_all("tr")[2:]

				# If the teacher doesn't implement categories
				if(len(categories) == 1):
					classes['category_summary'].append([['Assignments', '100.0', schedule['semester1']['total'][count].replace(" / ", "")]])
				# Otherwise, show categories
				else:
					summaryList = []
					for item in summaryCat:
						#if count == 4:
							#pprint(item.findChildren()[0].text)

						#if count == 4:
						#	print(summaryCat)

						#if count == 6:
							#print(summaryCat)

						temp = []
						temp.append(item.findChildren()[0].text)
						temp.append(item.findChildren()[1].text)
						temp.append(item.findChildren()[2].text.replace('\xa0', ''))
						summaryList.append(temp)

					classes['category_summary'].append(summaryList)
				
				# Category Details
				# if count == 3:
				# 	pprint(categories)

				browser.back()

	print("\nStudent data:")
	pprint(studentInfo)
	print("\nSchedule:")
	pprint(schedule)
	print("\nClasses:")
	pprint(classes)


	# print("\nCategories:")
	# for cat in classes['category_summary']:
	# 	print("---")
	# 	for c in cat:
	# 		print(c)

#def goToClass():

if __name__ == "__main__":
	if siteUp('https://dashboard.okaloosaschools.com/parentportal/PP000.pgm'):
		readConfig()
		main()
	else:
		print("Site not up")
# javascript:Send_Set_GrPd_Request('1');
# 	Send_Set_Schl_Request('0211');
# 	lnkProc('https://dashboard.okaloosaschools.com/parentportal/', '53753817031820170902122482973922', 
# 	'DP400', '', '', 'PP200', 
# 	'', '1001350', '001', '4602020856', 
# 	'495034725');

# https://dashboard.okaloosaschools.com/parentportal/DP400.pgm?SMURFID=53753817031820170902122482973922&rand=817017318

# https://dashboard.okaloosaschools.com/parentportal/PP200.pgm?SmurfId=53753817031820170902122482973922&rand=495034725