#!/usr/bin/env python
# coding: utf-8

# In[1]:


from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from bs4 import BeautifulSoup 
import re 
import time
import pandas as pd
import psycopg2
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
import os


# In[2]:


load_dotenv()
db_host = os.getenv('DB_HOST')
db_name = os.getenv('DB_NAME')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_port = os.getenv('DB_PORT')
username = os.getenv('IN_USERNAME')
mypassword = os.getenv('PASSWORD')
keywords = os.getenv('MOTS_CLES').split(',')


# In[3]:


try:
    connection = psycopg2.connect(
        host=db_host,
        database=db_name,
        user=db_user,
        port=db_port,
        password=db_password
    )
    cursor = connection.cursor()
    
    sql ='''CREATE TABLE IF NOT EXISTS INPOSTS(
    id SERIAL PRIMARY KEY,
    author VARCHAR(255),
    content TEXT,
    likes_count INT DEFAULT 0,
    comments_count INT DEFAULT 0,
    shares_count INT DEFAULT 0,
    post_date DATE,
    keywords VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP )'''
    cursor.execute(sql)
    connection.commit()
    cursor.close()
    print("Connexion réussie à la base de données")
    
except Exception as e:
    print(f"Erreur lors de la connexion à la base de données : {e}")
    raise


# In[4]:


driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))


# In[5]:


driver.get("https://www.linkedin.com/uas/login")
driver.maximize_window()
time.sleep(3)


# In[6]:


email=driver.find_element(By.ID,"username")
email.send_keys(username)
password=driver.find_element(By.ID,"password")
password.send_keys(mypassword)
time.sleep(3)
password.send_keys(Keys.RETURN)


# <h1>Il faut maintenant confirmer la connexion soit directement dans l'application mobile ou entrer sms dans le champ suivant</h1>

# <h2> Entrer sms si vous voulez verifier la connexion par sms ou appuyer entrer si vous l'avez faites sur un votre telephone</h2>

# In[7]:


confirmation = input("entrez sms si vous voulez verifier par sms sinon appuyer entrez si vous avez déjà confirmer") or "0"


# In[8]:


if confirmation == 'sms':
    code_validation = int(input ("Veuillez entrer le code recu par sms").strip())
    input_validation = driver.find_element(By.ID,"input__phone_verification_pin")
    input_validation.send_keys(code_validation)
    submit = driver.find_element(By.ID,"two-step-submit-button")
    submit.click()
    time.sleep(5)


# In[9]:


def clean_text(text):
    emoji_pattern = re.compile(
        "["               
        u"\U0001F600-\U0001F64F"  
        u"\U0001F300-\U0001F5FF"  
        u"\U0001F680-\U0001F6FF" 
        u"\U0001F700-\U0001F77F"  
        u"\U0001F780-\U0001F7FF"  
        u"\U0001F800-\U0001F8FF"  
        u"\U0001F900-\U0001F9FF"  
        u"\U0001FA00-\U0001FA6F"  
        u"\U0001FA70-\U0001FAFF"  
        u"\U00002700-\U000027BF"  
        u"\U00002600-\U000026FF"  
        "]+", flags=re.UNICODE
    )
    
    text = emoji_pattern.sub(r'', text)
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    text = re.sub(r'@\w+', '', text)
    text = re.sub(r'#\w+', '', text)
    text = re.sub(r'[^\w\s]', '', text)
    return text


# In[ ]:


while True:  
    for word in keywords:
        authors, contents, dates, likes, shares, comments = [], [], [], [], [], []
        search_input = driver.find_element(By.CLASS_NAME, "search-global-typeahead__input")
        search_input.clear()
        search_input.send_keys(word)
        search_input.send_keys(Keys.RETURN)
        time.sleep(3)
        
        try:
            see_all_posts = driver.find_element(By.LINK_TEXT, "Voir tous les résultats de posts")
            see_all_posts.click()
            time.sleep(2)
        except:
            pass
            
        start = time.time()
        now = datetime.now()
        lastHeight = driver.execute_script("return document.body.scrollHeight")
        
        while True:
            see_more_elements = driver.find_elements(By.XPATH, "//span[text()='… plus']")
            for element in see_more_elements:
                try:
                    element.click()
                    time.sleep(1)
                except:
                    pass
            
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(7)  
            newHeight = driver.execute_script("return document.body.scrollHeight")
        
            if newHeight == lastHeight:
                break
            lastHeight = newHeight
            
            if round(time.time() - start) > 300:
                break
        
        result = driver.page_source
        soup = BeautifulSoup(result.encode("utf-8"), "html.parser")
        
        authors_span = soup.find_all('span', class_='update-components-actor__name')
        contents_span = soup.find_all('span', class_='break-words tvm-parent-container')
        dates_span = soup.find_all('span', class_='update-components-actor__sub-description')
        likes_span= soup.find_all('span', class_='social-details-social-counts__reactions-count')
        comments_span = soup.find_all('span', string=re.compile('commentaire|commentaires'))
        shares_span =soup.find_all('span', class_='social-details-social-counts__item--truncate-text')
        
        for author ,content, like ,share, comment in zip (authors_span ,contents_span ,likes_span ,shares_span ,comments_span ):
            item1 = author.get_text(strip=True).split()[0]
            item2 = clean_text(content.get_text(strip=True))
            item3 = like.get_text(strip=True)
            item4 = share.get_text(strip=True).split()[0]
            item5 = comment.get_text(strip=True).split()[0]
            authors.append(item1)
            contents.append(item2)
            likes.append(item3)
            shares.append(item4)
            comments.append(item5)

        
        for date in dates_span:
            item = date.get_text().strip()
        
            if 'il y a' not in item:
                if 'j' in item:
                    days = int(re.search(r'(\d+)\s*j', item).group(1))
                    new_date = (now - timedelta(days=days)).strftime('%Y-%m-%d')
                    dates.append(new_date)
        
                elif 'h' in item:
                    hours = int(re.search(r'(\d+)\s*h', item).group(1))
                    new_date = (now - timedelta(hours=hours)).strftime('%Y-%m-%d')
                    dates.append(new_date)
        
                elif 'sem.' in item:
                    weeks = int(re.search(r'(\d+)\s*sem\.', item).group(1))
                    new_date = (now - timedelta(weeks=weeks)).strftime('%Y-%m-%d')
                    dates.append(new_date)
        
                elif 'mois' in item:
                    months = int(re.search(r'(\d+)\s*mois', item).group(1))
                    new_date = (now - relativedelta(months=months)).strftime('%Y-%m-%d')
                    dates.append(new_date)
                    
        cursor = connection.cursor()
        
        for author, content, like, share, comment ,post_date in zip (authors , contents ,likes ,shares,comments, dates):
            sql_check = '''SELECT COUNT(*) FROM INPOSTS WHERE author = %s AND content = %s AND post_date = %s'''
            sql_insert = '''INSERT INTO INPOSTS (author, content ,likes_count, shares_count,comments_count, post_date, keywords) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s)'''
            cursor.execute(sql_check, (author, content, post_date))
            exists = cursor.fetchone()[0]
            if exists == 0:  
                try:
                    cursor.execute(sql_insert, (author, content, like, share, comment, post_date, word))
                    connection.commit()
                    print(f"Post ajouté: {author} - {content} - {post_date} -{word} \n")
                except Exception as e:
                    print(f"Erreur lors de l'insertion du post: {e}")
                    connection.rollback()

            else:
                print("Ce post existe déjà")

        cursor.close()
        time.sleep(10)


# In[ ]:




