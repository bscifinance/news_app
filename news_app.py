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
from pathlib import Path
import yaml
from yaml.loader import SafeLoader

st.set_page_config(page_title="BSCI_News", page_icon="logo_bsci.png", layout="wide")

with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

def scrape_news(topic, period, language):
    # replace spaces with +
    topic = topic.replace(' ', '+')
    
    if language == "Spanish" and period == "Última hora":
        url = f'https://news.google.com/search?q={topic}+when:1h&hl=es-419&gl=CL&ceid=CL:es-419'
    elif language == "Spanish" and period == "Últimas 24 horas":
        url = f'https://news.google.com/search?q={topic}+when:1d&hl=es-419&gl=CL&ceid=CL:es-419'
    elif language == "Spanish" and period == "Última semana":
        url = f'https://news.google.com/search?q={topic}+when:7d&hl=es-419&gl=CL&ceid=CL:es-419'
    elif language == "Spanish" and period == "Últimos 30 días":
        url = f'https://news.google.com/search?q={topic}+when:1m&hl=es-419&gl=CL&ceid=CL:es-419'
    elif language == "Spanish" and period == "Últimos seis meses":
        url = f'https://news.google.com/search?q={topic}+when:6m&hl=es-419&gl=CL&ceid=CL:es-419'
    elif language == "Spanish" and period == "Último año":
        url = f'https://news.google.com/search?q={topic}+when:1y&hl=es-419&gl=CL&ceid=CL:es-419'
    elif language == "Spanish" and period == "Cualquiera":
        url = f'https://news.google.com/search?q={topic}&hl=es-419&gl=CL&ceid=CL:es-419'
    elif language == "English" and period == "Última hora":
        url = f'https://news.google.com/search?q={topic}+when:1h&hl=en-US&gl=US&ceid=US:en'
    elif language == "English" and period == "Últimas 24 horas":
        url = f'https://news.google.com/search?q={topic}+when:1d&hl=en-US&gl=US&ceid=US:en'
    elif language == "English" and period == "Última semana":
        url = f'https://news.google.com/search?q={topic}+when:7d&hl=en-US&gl=US&ceid=US:en'
    elif language == "English" and period == "Últimos 30 días":
        url = f'https://news.google.com/search?q={topic}+when:1m&hl=en-US&gl=US&ceid=US:en'
    elif language == "English" and period == "Últimos seis meses":
        url = f'https://news.google.com/search?q={topic}+when:6m&hl=en-US&gl=US&ceid=US:en'
    elif language == "English" and period == "Último año":
        url = f'https://news.google.com/search?q={topic}+when:1y&hl=en-US&gl=US&ceid=US:en'
    else:
        url = f'https://news.google.com/search?q={topic}&hl=en-US&gl=US&ceid=US:en'

    # scrape webpage
    page = requests.get(url).text
    soup = BeautifulSoup(page, 'html.parser')

    #extract info
    result_tl = soup.select('article .DY5T1d.RZIKme')
    title = [t.text for t in result_tl]
    
    result_dt = soup.select('[datetime]')
    timedate = [d.text for d in result_dt]
    
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
   for url, source, timedate in zip(url_list, df['source'][:num],df['timedate'][:num]):
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
          'date': timedate,
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

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

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
col1, col2 = st.columns([1, 3])

if authentication_status == False:
    st.error("Username/password is incorrect")

if authentication_status == None:
    st.warning("Please enter your username and password") 

if authentication_status:
    
    authenticator.logout("Logout", "main")

    col1.image("logo_bsci.png", width=100)
    col1.title("BSCI News")
    col1.markdown("Resumen de noticias a tu medida")
    col1.markdown("Ingresa un tópico para buscar artículos de noticias y elige cuantos resúmenes quieres desplegar:")
    topic = col1.text_input("Tópico")
    num_summaries = col1.slider("Número de resúmenes a desplegar", 5, 20, 5)
    selected_date = col1.selectbox("Elige la fecha", ["Cualquiera","Última hora", "Últimas 24 horas", "Última semana", "Últimos 30 días", "Últimos seis meses", "Último año"])
    language = col1.selectbox("Elige el Idioma", ["English", "Spanish"])
    if language == 'English':
        lang = 'en'
    else:
        lang = 'es'
    
    if col1.button("Search"):
        df = scrape_news(topic, selected_date, language)

        news_list = summarize_news(df, num_summaries)
        col2.write(f"Desplegando {len(news_list)} resumenes de noticias:")

        for i, news in enumerate(news_list):
            col2.write(f"Title: [{news['title']}]({news['link']})")
            col2.write(f"Source: {news['source']}")
            col2.write(f"Time and Date: {news['date']}")
            col2.write(f"Summary: {news['summary']}")
            col2.write("----")
            col2.audio(play_audio(news['summary'], lang), format='audio/mp3')



