import requests
import sys
import config as cfg
import clearbit
import json
import time
import hashlib
from bs4 import BeautifulSoup
import re
from email_fullcontact import fullcontact
from termcolor import colored
class style:
   BOLD = '\033[1m'
   END = '\033[0m'

if len(sys.argv) < 2 :
	sys.exit("[-] No argument passed. \nUsage: domainOsint.py [options]\n\nOptions:\n  -h,\t\t--help\t\t\tshow this help message and exit\n  -d DOMAIN,\t--domain=DOMAIN\t\tDomain name against which automated Osint is to be performed.")
email = sys.argv[1]
username_list = []

def check_and_append_username(username):
	if username not in username_list:
		username_list.append(username)


def haveIbeenpwned(email):
	print colored(style.BOLD + '\n---> Checking breach status in HIBP (@troyhunt)\n' + style.END, 'blue')
	time.sleep(0.3)
	req = requests.get("https://haveibeenpwned.com/api/v2/breachedaccount/%s" % (email))
	if req.content != "":
		return json.loads(req.content)
	else:
		return {}


def clearbit(email):
	header = {"Authorization" : "Bearer %s" % (cfg.clearbit_apikey)}
	req = requests.get("https://person.clearbit.com/v1/people/email/%s" % (email), headers = header)
	person_details = json.loads(req.content)
	if ("error" in req.content and "queued" in req.content):
		print "This might take some more time, Please run this script again, after 5 minutes."
		time.sleep(20)
	else:
		return person_details

def gravatar(email):
	gravatar_url = "http://www.gravatar.com/avatar/" + hashlib.md5(email.lower()).hexdigest() 
	return gravatar_url

def emaildom(email):
	req = requests.get('http://www.whoismind.com/email/%s.html'%(email))
	soup=BeautifulSoup(req.content, "lxml")
	atag=soup.findAll('a')
	domains=[]
	for at in atag:
		if at.text in at['href']:
			domains.append(at.text)
	domains=set(domains)
	return domains

def emailslides(email):
	req = requests.get('http://www.slideshare.net/search/slideshow?q=%s'%(email))
	soup=BeautifulSoup(req.content, "lxml")
	atag=soup.findAll('a',{'class':'title title-link antialiased j-slideshow-title'})
	slides={}
	for at in atag:
		slides[at.text]=at['href']
	return slides

def emailscribddocs(email):
	req = requests.get('https://www.scribd.com/search?page=1&content_type=documents&query=%s'%(email))
	soup=BeautifulSoup(req.content, "lxml")
	m = re.findall('(?<=https://www.scribd.com/doc/)\w+', req.text.encode('UTF-8'))
	m = set(m)
	m = list(m)
	links=[]
	length=len(m)
	for lt in range(0,length-1):
		links.append("https://www.scribd.com/doc/"+m[lt])
	return links


def list_down_usernames():
	if len(username_list) != 0:
		print colored(style.BOLD + '\n---> Enumerated Usernames\n' + style.END, 'blue')
		for x in username_list:
			print x
		print "\n"

	
def print_emailosint(email):
	hbp = haveIbeenpwned(email)
	if len(hbp) != 0:
		print colored("Pwned at %s Instances\n", 'green') % len(hbp)
		for x in hbp:
			print "Title:%s\nBreachDate%s\nPwnCount%s\nDescription%s\nDataClasses%s\n" % (x.get('Title', ''), x.get('BreachDate', ''), x.get('PwnCount', ''), x.get('Description', ''),x.get('DataClasses', ''))
	else:
		print colored("[-] No breach status found.", 'red')

	print colored(style.BOLD + '\n---> Finding User Information\n' + style.END, 'blue')
	time.sleep(0.3)
	data = fullcontact(email)
	if data.get("status","") == 200:
		if data.get("contactInfo","") != "":
			print "Name: %s" % data.get("contactInfo","").get('fullName', '')
		print colored(style.BOLD + '\n Organizations / Work History\n' + style.END, 'green')
		for x in data.get("organizations",""):
			if x.get('isPrimary', '') == True:
				primarycheck = " - Primary"
			else:
				primarycheck = ""
			if x.get('endDate','') == '':
				print "\t%s at %s - (From %s to Unknown Date)%s" % (x.get('title', ''), x.get('name',''), x.get('startDate',''), primarycheck)
			else:
				print "\t%s - (From %s to %s)%s" % (x.get('name',''), x.get('startDate',''), x.get('endDate',''), primarycheck)
		if data.get("contactInfo","") != "":
			if data.get("contactInfo","").get('websites', '') != "":
				print "\nWebsite(s):"
				for x in data.get("contactInfo","").get('websites', ''):
					print "\t%s" % x.get('url', '')
			if data.get("contactInfo","").get('chats', '') != "":
				print '\nChat Accounts'
				for x in data.get("contactInfo","").get('chats', ''):
					print "\t%s on %s" % (x.get('handle', ''), x.get('client', ''))
		
		print colored(style.BOLD + '\n Social Profiles\n' + style.END, 'green')
		for x in data.get("socialProfiles",""):
			head = "\t%s:" % x.get('type','').upper()
			print colored(style.BOLD + str(head) + style.END)
			for y in x.keys():
				if y != 'type' and y != 'typeName' and y != 'typeId':
					print '\t%s: %s' % (y, x.get(y,''))
			if x.get('username', '') != "":
				check_and_append_username(x.get('username', ''))

			print ''

		print colored(style.BOLD + '\n Other Details\n' + style.END, 'green')
		if data.get("demographics","") != "":
			print "\tGender: %s" % data.get("demographics","").get('gender', '')
			print "\tCountry: %s" % data.get("demographics","").get('country', '')
			print "\tTentative City: %s" % data.get("demographics","").get('locationGeneral', '')

		print "Photos:"
		for x in data.get("photos",""):
			print "\t%s: %s" % (x.get('typeName', ''), x.get('url', ''))

	else:
		print colored('[-] Error Occured - Encountered Status Code: %s. Please check if Email_id exist or not?', 'red') % data.get("status","")



	'''clb_data = clearbit(email)
	for x in clb_data.keys():
		print '%s details:' % x
		if type(clb_data[x]) == dict:
			for y in clb_data[x].keys():
				if clb_data[x][y] is not None:
					print "%s:  %s, " % (y, clb_data[x][y])
		elif clb_data[x] is not None:
			print "\n%s:  %s" % (x, clb_data[x])

	print "\n-----------------------------\n"

	print "\t\t\t[+] Gravatar Link\n"
	print gravatar(email)
	print "\n-----------------------------\n"

	print "\t\t\t[+] Associated Domains\n"
	for doms in emaildom(email):
		print doms
	'''

	
	slds=emailslides(email)
	if len(slds) != 0:
		print colored(style.BOLD + '\n---> Slides Published:' + style.END, 'blue')
		time.sleep(0.3)
		for tl,lnk in slds.items():
			print tl+"http://www.slideshare.net"+lnk
	else:
		print colored('[-] No Associated Slides found.', 'red')

	
	scdlinks=emailscribddocs(email)
	if len(scdlinks) != 0:
		print colored(style.BOLD + '\n---> Associated SCRIBD documents:\n' + style.END, 'blue')
		time.sleep(0.5)
		for sl in scdlinks:
			print sl
		print ""
		print colored(style.BOLD + 'More results might be available:' + style.END)
		print "https://www.scribd.com/search?page=1&content_type=documents&query="+email
	else:
		print colored('[-] No Associated Scribd Documents found.', 'red')




def main():
	print_emailosint(email)
	list_down_usernames()
	
if __name__ == "__main__":
	main()

