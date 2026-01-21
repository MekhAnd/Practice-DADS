# STAT(RAG)BOT PROJECT

* ### School
* ### Instructors
* ### Legend
* ### How It Works
* ### Tools & Technologies
* ### Installation & Setup


**Deathworld Statistics** is a RAG-powered chatbot that teaches statistics through the immersive persona of **Professor Jason Dean Alt**.

Instead of dry textbook definitions, this bot uses the **Llama 3.3 (70b)** model via **Groq** to weave rigorous mathematical concepts into a narrative. It analyzes the context to determine the professor's "mood" and explains math using specific anecdotes from his life in a harsh environment.

---

## Legend: Who is the Professor?

The user acts as a student interacting with **Jason Dean Alt**, a brilliant but distinct statistics teacher.

* **Behavior:** The bot analyzes the conversation history to derive its current emotional state and teaching style.
* **Narrative Learning:** Mathematical answers are illustrated using specific anecdotes, daily struggles, and examples from Jason's personal "world."
* **Goal:** To transform statistics from a dry subject into an engaging, character-driven narrative experience.

---

## How It Works

This application uses a local-first retrieval approach paired with a high-speed inference engine:

1. **Ingestion:** Scans `data/content/` for course materials.
2. **Local Vectorization:** Uses **HuggingFace** (`all-MiniLM-L6-v2`) to convert text into embeddings locally on the CPU.
3. **Storage:** Vectors are persisted in `data/vector_index` to avoid re-indexing.
4. **Retrieval:** Fetches the top 2 most relevant context chunks.
5. **Inference:** Uses **Groq** (hosting Llama 3.3) for fast, character-driven responses.

---

## Tools & Technologies

* **Interface:** [Streamlit](https://streamlit.io/)
* **Orchestration:** [LlamaIndex](https://www.llamaindex.ai/)
* **LLM Provider:** [Groq](https://groq.com/) (Model: `llama-3.3-70b-versatile`)
* **Embeddings:** HuggingFace `sentence-transformers` (Local CPU execution)
* **NLP Tools:** NLTK (Punkt, Stopwords)

---

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/statbot.git
cd statbot

```

### 2. Set Up Virtual Environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Mac/Linux
python3 -m venv .venv
source .venv/bin/activate

```

### 3. Install Dependencies

```bash
pip install streamlit llama-index llama-index-llms-groq llama-index-embeddings-huggingface torch nltk transformers

```

### 4. Project Structure

Ensure your folder structure matches the code exactly:

```text
/Stat_bot
├── .streamlit
│   └── secrets.toml    <-- API Keys go here (See step 5)
├── data
│   ├── content         <-- PUT YOUR PDF/TXT FILES HERE (All of Statistics)
│   ├── vector_index    <-- Created automatically (Index storage)
│   └── embd_fld        <-- Created automatically (Model cache)
└── statbot.py          <-- Main application

```

### 5. Configure Secrets (Crucial!)

This app uses **Streamlit Secrets** instead of environment variables.

1. Create a folder named `.streamlit` in your project root.
2. Inside it, create a file named `secrets.toml`.
3. Add your Groq API key:

```toml
# .streamlit/secrets.toml
GROQ_API_KEY = "xxx_..."

```

*(You can get a free API key at [console.groq.com](https://console.groq.com/))*

### 6. Run the App

```bash
streamlit run statbot.py

```

*Note: The first run will download the embedding model and NLTK data, which may take a minute.*

---

## Troubleshooting

* **"No files found"**: Ensure you have actual files inside `data/content/`.
* **"secrets.toml not found"**: Make sure the `.streamlit` folder is in the same directory where you are running the command.
* **Device Warning**: The code is forced to run embeddings on `device="cpu"`. If you want to use a GPU, change line 33 in `statbot.py` to `device="cuda"`.

---

## 📜 License

[MIT](https://choosealicense.com/licenses/mit/)