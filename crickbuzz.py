import requests
import bs4
from plyer import notification
import time

link='https://www.cricbuzz.com/live-cricket-scores/46081/srh-vs-gt-40th-match-indian-premier-league-2022'

start=time.time()

while True:

	res=requests.get(link)

	soup=bs4.BeautifulSoup(res.text,'html.parser') # entire source code of website

	details=soup.select('.cb-col .cb-col-67 .cb-scrs-wrp') # dot is placed to represent it as a class

	for i in details:

		# print(i.getText())
		notification.notify(title='Cricket Score',message=i.getText(),app_icon='a.ico',timeout=5)
	
	if time.time()-start > 300:
		break
	time.sleep(100)
print('DONE')