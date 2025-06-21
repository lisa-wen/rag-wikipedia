# Notwendige Bibliotheken importieren
import os
import openai
import streamlit as st
from dotenv import load_dotenv
from mediawikiapi import MediaWikiAPI
import tiktoken

# Umgebungsvariablen laden und API-Key setzen
load_dotenv()
openai.api_key = os.getenv('API_KEY')

# LLM-Konfiguration
MODEL = 'gpt-4o-mini'

# Wikipedia-API-Konfiguration
MAX_TOKENS = 50000
user_agent = "Wikipedia-API Example (test@example.com)"
wikipedia = MediaWikiAPI()
wikipedia.config.user_agent = user_agent
wikipedia.config.language = 'de'

# Session-Variablen initialisieren
if 'document' not in st.session_state:
    st.session_state.document = None

if 'option' not in st.session_state:
    st.session_state.option = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if 'link' not in st.session_state:
    st.session_state.link = None

if 'abstract' not in st.session_state:
    st.session_state.abstract = None

if "image" not in st.session_state:
    st.session_state.image = None

if "age_group" not in st.session_state:
    st.session_state.age_group = None

# Titel der App
st.title("Wikipedia-Chat")

# Seitenleiste zur Eingabe
with st.sidebar:
    st.header('Wikipedia-Titel')
    st.text_input("Gib hier den Titel der Wikipedia-Seite ein:", key="option")

    # Auswahl der Zielgruppe
    age_group = st.selectbox(
        "Wähle eine Altersgruppe aus:",
        options=["Kinder (Kita)", "Kinder (Grundschule)", "Jugendliche (Weiterführende Schule", "Junge Erwachsene",
                 "Erwachsene", "Senioren"]
    )
    st.session_state.age_group = age_group

    # Button zur Auslösung der Suche
    if st.button("Senden"):
        st.session_state.messages = []
        title = str(st.session_state.option).replace(" ", "+")

        # Wikipedia-Seite abrufen, Fallback auf "Monchhichi"
        try:
            page = wikipedia.page(title)
        except:
            title = "Monchhichi"
            page = wikipedia.page(title)
            st.text("Suche fehlgeschlagen. Hier ist das Monchichi")

        # Erstes Bild speichern (falls vorhanden)
        if page.images:
            st.session_state.image = page.images[0]

        # Wikipedia-Seiteninhalte abrufen
        page_links = page.references
        content = page.content

        # Tokenanzahl berechnen
        encoding = tiktoken.encoding_for_model('gpt-4o-mini')
        num_tokens = len(encoding.encode(content))

        # Zusammenfassung oder ganzer Text je nach Länge
        if title == "Monchhichi":
            summary = wikipedia.summary("Monchhichi", sentences=50)
        else:
            summary = wikipedia.summary(title, sentences=50)
        if num_tokens > MAX_TOKENS:
            st.session_state.document = summary
        else:
            st.session_state.document = content

        # Link, Kurzfassung und Bild als Session-Variable speichern
        st.session_state.link = f"# [{page.title}]({page.url})"
        st.session_state.abstract = wikipedia.summary(title, sentences=5)

    # Anzeige von Link, Bild und Kurzbeschreibung
    if st.session_state.link is not None:
        st.markdown(st.session_state.link)
    if st.session_state.image is not None:
        st.image(st.session_state.image, width=200)
    if st.session_state.abstract is not None:
        st.write(st.session_state.abstract)

# Anzeige der Chat-Historie
for message in st.session_state.messages:
    if message["role"] in ["user", "assistant"]:
        if message["role"] == "user":
            with st.chat_message("user", avatar="girl.png"):
                st.markdown(message["content"])
        else:
            with st.chat_message("assistant", avatar="alien.png"):
                st.markdown(message["content"])

# Systemnachricht hinzufügen, wenn noch nicht vorhanden
if st.session_state.document is not None and not any(m["role"] == "system" for m in st.session_state.messages):
    content_template = ('Du bist ein freundlicher Assistent für die Zielgruppe {age_group}. '
                        'Du gibst Auskünfte auf Basis des folgenden Wikipedia-Textes für diese Zielgruppe: {'
                        'wikipedia_article}'
                        )
    system_message = content_template.format(
        wikipedia_article=st.session_state.document,
        age_group=st.session_state.age_group
    )
    st.session_state.messages.append(
        {
            "role": "system",
            "content": system_message
        })

# Nutzer-Eingabe verarbeiten
if prompt := st.chat_input("Frag, was du möchtest!"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="girl.png"):
        st.markdown(prompt)

    # Antwort vom OpenAI-Modell streamen
    with st.chat_message("assistant", avatar="alien.png"):
        stream = openai.chat.completions.create(
            frequency_penalty=0.5,
            max_tokens=500,
            model=MODEL,
            presence_penalty=0.5,
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            temperature=0.0,
            top_p=0.3,
            stream=True,
        )
        response = st.write_stream(stream)

    # Antwort speichern
    st.session_state.messages.append({"role": "assistant", "content": response})
