from bs4 import BeautifulSoup
from urllib.parse import urljoin
import requests
import pandas as pd
import newspaper
from newspaper import Article
import nltk
nltk.download('punkt')
import streamlit as st
import streamlit_authenticator as stauth
from gtts import gTTS
from IPython.display import Audio, display
import io
import datetime
import pickle
from pathlib import Path
import yaml
from yaml.loader import SafeLoader

st.set_page_config(page_title="BSCI_News", page_icon="logo_bsci.png")

with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

def scrape_news(topic, language):
    # replace spaces with +
    topic = topic.replace(' ', '+')
    
    if language == "Spanish":
        url = f'https://news.google.com/search?q={topic}&hl=es-419&gl=CL&ceid=CL:es-419'
    else:
        url = f'https://news.google.com/search?q={topic}&hl=en-US&gl=US&ceid=US:en'
   
    # scrape webpage
    page = requests.get(url).text
    soup = BeautifulSoup(page, 'html.parser')

    #extract info
    result_tl = soup.select('article .DY5T1d.RZIKme')
    title = [t.text for t in result_tl]
    
    result_dt = soup.select('[datetime]')
    timedate = [d['datetime'] for d in result_dt]
    
    result_src = soup.select('article .wEwyrc.AVN2gc.WfKKme')
    source = [s.text for s in result_src]

    links = []
    base_url = 'https://news.google.com/'
    for i in soup.select('article .DY5T1d.RZIKme'):
        ss = urljoin(base_url, i.get('href'))
        # put all absolute links into empty list
        links.append(ss) 

    # putting all of data into a list
    all_data = list(zip(source, title, timedate, links))

    # convert the list into dataframe
    df = pd.DataFrame(all_data, columns=['source', 'title', 'timedate', 'links'])

    return df

def summarize_news(df, num):
   url_list =  list(df["links"])[:num]
   news_list = []
   for url, source in zip(url_list, df['source'][:num]):
   #for url in url_list:
      article = Article(url, keep_article_html=True)
      try:
         article.download()
         article.parse()
         article.nlp()
      except:
         pass 
      story = {
          'title': article.title.replace('\n',''),
          'source': source,
          'date': article.publish_date,
          'link': url,
          'text': article.text.replace('\n',''),
          'summary': article.summary.replace('\n','').replace('.','. ')
          }
      news_list.append(story)
   return news_list

def play_audio(summary, lang):
    if not summary:
        return None
    # Generate audio file from summary
    tts = gTTS(summary, lang=lang)
    audio_bytes = io.BytesIO()
    tts.write_to_fp(audio_bytes)
    return audio_bytes.getvalue()

def log_activity(username):
    # Get the current date and time
    now = datetime.datetime.now()

    # Open the log file
    with open("log.txt", "a") as f:
        # Write the username and timestamp to the log file
        f.write(f"{username} logged in at {now}\n")

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)
# authenticator = stauth.Authenticate(names, usernames, hashed_passwords, "bsci_news", "abcdef")

name, authentication_status, username = authenticator.login("Login", "main")

hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            footer:after {
                content:'Powered by: googlenews'; 
                visibility: visible;
                display: block;
                position: relative;
                #background-color: red;
                padding: 5px;
                top: 2px;
            }
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

if authentication_status == False:
    st.error("Username/password is incorrect")

if authentication_status == None:
    st.warning("Please enter your username and password") 

if authentication_status:
    log_activity(username)

    authenticator.logout("Logout", "sidebar")

    st.sidebar.image("logo_bsci.png", width=200)
    st.sidebar.title("BSCI News")
    st.sidebar.markdown("Resumen de noticias a tu medida")
    st.sidebar.caption('''
                **Credits**
                - App desarrollada por bsci.finance'''
                )
    st.sidebar.markdown("Ingresa un tópico para buscar artículos de noticias y elige cuantos resumenes quieres desplegar:")
    topic = st.sidebar.text_input("Tópico")
    num_summaries = st.sidebar.slider("Número de resumenes a desplegar", 5, 20, 5)
    language = st.sidebar.selectbox("Elige el Idioma", ["English", "Spanish"])
    if language == 'English':
        lang = 'en'
    else:
        lang = 'es'
    if st.sidebar.button("Search"):
        if language == 'English':
            df = scrape_news(topic, 'English')
        else:
            df = scrape_news(topic, 'Spanish')    
        news_list = summarize_news(df, num_summaries)
        st.write(f"Desplegando {len(news_list)} resumenes de noticias:")

        for i, news in enumerate(news_list):
            st.write(f"Title: [{news['title']}]({news['link']})")
            st.write(f"Source: {news['source']}")
            st.write(f"Time and Date: {news['date']}")
            st.write(f"Summary: {news['summary']}")
            st.write("----")
            st.audio(play_audio(news['summary'], lang), format='audio/mp3')




