# shift + enter -> for new line
# ctrl + l and backspace enter new url to do in a while loop for many contacts
import pyautogui
import webbrowser
from time import sleep
# Path to your Chrome executable
chrome_path = 'C:/Program Files/Google/Chrome/Application/chrome.exe'
webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(chrome_path))
country_code = '91'
mob_no = '8074128388'
url = "web.whatsapp.com/send?phone="+country_code+mob_no
webbrowser.get('chrome').open(url)
sleep(8)
position = pyautogui.locateOnScreen('search_box.png', confidence=0.5)
pyautogui.FAILSAFE = False
pyautogui.moveTo(position.left, position.top, duration=0.1)
pyautogui.leftClick()
f = open('message.txt')
text = f.read()
for i in text:
    if i == '\n' or i == '\r':
        pyautogui.hotkey('shift', 'enter')
    else:
        pyautogui.write(i)
pyautogui.press('enter')
