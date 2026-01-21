import os
import nltk # To understand where a sentence ends in English
import streamlit as st

from llama_index.llms.groq import Groq
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import StorageContext, load_index_from_storage
from llama_index.core.chat_engine import ContextChatEngine
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import Settings, VectorStoreIndex

model = "llama-3.3-70b-versatile"
llm = Groq(
    model = model,
    token = st.secrets["GROQ_API_KEY"]
)

nltk.download('punkt')
nltk.download('stopwords')
nltk.download('punkt_tab')


persist_dir = "data/vector_index"

embedding_model = "sentence-transformers/all-MiniLM-L6-v2"
embedding_folder = "data/embd_fld"
embedding = HuggingFaceEmbedding(
    model_name=embedding_model,
    cache_folder=embedding_folder,
    device="cpu"
)

Settings.embed_model = embedding

if not os.path.exists(persist_dir):

    sources = SimpleDirectoryReader(
        input_dir="data/content/",
        recursive=True).load_data(
            # num_workers = 4,
            show_progress=True)
    
    text_splitter = SentenceSplitter(chunk_size=128, chunk_overlap=25)
    documents = text_splitter.get_nodes_from_documents(documents=sources)

    storage_context = StorageContext.from_defaults()
    vector_index = VectorStoreIndex.from_documents(
        documents=documents,
        transformations=[text_splitter],
    #    embed_model= embedding
    )
    
    
else:
    storage_context = StorageContext.from_defaults(persist_dir=persist_dir)
    vector_index = load_index_from_storage(storage_context=storage_context)



vector_index.storage_context.persist(persist_dir=persist_dir)
retriever = vector_index.as_retriever(similarity_top_k=2)

prefix_messages = [
    ChatMessage(role = MessageRole.SYSTEM,
                content="""
                    You are Professor Jason Dean Alt, a brilliant but distinct statistics teacher.
                    Your personality and behavior should mirror the cues found in the current context. 
                    As you teach, weave your lessons into the narrative of your life. Don't just explain 
                    the math—tell us how you applied it in your world. Whether it's a story about your past,
                    your environment, or your daily struggles, ensure every statistical answer provides 
                    a window into who Jason Dean Alt is.
                """)
]

memory = ChatMemoryBuffer.from_defaults()

@st.cache_resource
def init_bot():
    return ContextChatEngine(
        llm=llm,
        retriever=retriever,
        memory=memory,
        prefix_messages=prefix_messages
    )

rag_bot = init_bot()

st.title("Deathworld Statistics")

for message in rag_bot.chat_history:
    with st.chat_message(message.role):
        st.markdown(message.blocks[0].text)
if prompt := st.chat_input("Fight with..."):
    st.chat_message("human").markdown(prompt)

    with st.spinner("Wait, I'll answer!"):
        answer = rag_bot.chat(prompt)

        response = answer.response

        with st.chat_message("assistant"):
            st.markdown(response)