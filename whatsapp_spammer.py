import pyautogui
import time
time.sleep(4)
count=0
while count<10:
    pyautogui.typewrite('Hi good morning',str(count))
    pyautogui.press('enter')
    count+=1