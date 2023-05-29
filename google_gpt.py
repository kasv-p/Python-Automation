# here, system - 1st sets the context
# later user can ask the question
# but to keep up the history one can use assistant role in which we can include the content give by the chatgpt model
# later we take user input again but see we have the affect of previous history also as we add role assistand and prev given answer to the message being sent

# example
'''

while True:
    message = input("User : ")
    if message:
        messages.append(
            {"role": "user", "content": message},
        )
        chat = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", messages=messages
        )
      
    reply = chat.choices[0].message.content
    print(f"ChatGPT: {reply}")
    messages.append({"role": "assistant", "content": reply})

'''

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import openai


def chat_gpt(texts):
    openai.api_key = "<API_KEY>"
    response = openai.ChatCompletion.create(model='gpt-3.5-turbo', messages=[
                                            {"role": "system", "content": texts}])
    return response.choices[0]['message']['content']


urls, text = [], ''

query = 'what are the crazy things you do when you are bored'.replace(' ', '+')
search_query = 'https://www.google.com/search?q='+query
options = Options()
options.add_argument('--headless')
options.add_argument('--log-level=1')
driver = webdriver.Chrome(
    r"C:/Users/DELL/Downloads/chromedriver_win32/chromedriver.exe", options=options)
driver.get(search_query)
links = driver.find_elements(By.CLASS_NAME, 'yuRUbf')

for link in links[:2]:
    anchor = link.find_element(By.XPATH, 'a')
    urls.append(anchor.get_attribute('href'))
print(urls)
for url in urls:
    text = 'Generate a summary from the following url:'+url
    text += chat_gpt(text)
result = chat_gpt('generate a detailed summary from: {}'.format(
    text)).replace(". ", ".\n")
print("summary of req output :\n", result)
