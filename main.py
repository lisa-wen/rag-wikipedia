import os
import openai
import streamlit as st
from dotenv import load_dotenv
from mediawikiapi import MediaWikiAPI
import tiktoken

load_dotenv()

openai.api_key = os.getenv('API_KEY')
user_agent = "Wikipedia-API Example (test@example.com)"
MODEL = 'gpt-4o-mini'
MAX_TOKENS = 40000

wikipedia = MediaWikiAPI()
wikipedia.config.user_agent = user_agent
wikipedia.config.language = 'de'

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

st.title("Wikipedia-Chat")

with st.sidebar:
    st.header('Wikipedia-Titel')
    st.text_input("Gib hier den Titel der Wikipedia-Seite ein:", key="option")
    if st.button("Senden"):
        st.session_state.messages = []
        page = wikipedia.page(st.session_state.option)
        if page.images:
            st.session_state.image = page.images[0]
        page_links = page.references
        content = page.content
        encoding = tiktoken.encoding_for_model('gpt-4o-mini')
        num_tokens = len(encoding.encode(content))
        if num_tokens > MAX_TOKENS:
            st.session_state.document = wikipedia.summary(st.session_state.option, sentences=50)
        else:
            st.session_state.document = content
        st.session_state.link = f"# [{page.title}]({page.url})"
        st.session_state.abstract = wikipedia.summary(st.session_state.option, sentences=5)

    if st.session_state.link is not None:
        st.markdown(st.session_state.link)
    if st.session_state.image is not None:
        st.image(st.session_state.image, width=200)
    if st.session_state.abstract is not None:
        st.write(st.session_state.abstract)

for message in st.session_state.messages:
    if message["role"] in ["user", "assistant"]:
        if message["role"] == "user":
            #with st.chat_message("user", avatar=""):
            with st.chat_message("user"):
                st.markdown(message["content"])
        else:
            #with st.chat_message("assistant", avatar=""):
            with st.chat_message("assistant"):
                st.markdown(message["content"])

content_start = "Du gibst Auskünfte auf Basis der Fakten in nachfolgendem Text:"
content_end = '' if st.session_state.document is None else st.session_state.document
st.session_state.messages.append({"role": "system", "content": content_start+content_end})

if prompt := st.chat_input("Frag, was du möchtest!"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    #with st.chat_message("user", avatar=""):
    with st.chat_message("user"):
        st.markdown(prompt)

    #with st.chat_message("assistant", avatar="alien.png"):
    with st.chat_message("assistant"):
        stream = openai.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            temperature=0.0,
            stream=True,
        )
        response = st.write_stream(stream)
    st.session_state.messages.append({"role": "assistant", "content": response})

