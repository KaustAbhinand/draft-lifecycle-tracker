This is a draft lifecycle tracker agent, that tracks the lifecycle states of a draft (specifically, an email draft) viz. **OPEN**, **CONVERTED**, **CONVERTED_EDITED**, **EXPIRED**.

### Setup
- Fork the repo
- Clone it (do it from the VS code IDE)
- Create a virtual environment - python -m venv .venv
- Activate the virtual environment: venv\Scripts\activate.
- Install the dependencies: **pip install -r requirements.txt**
- Add a .env file, include the API key like this: **GROQ_API_KEY = (YOUR_KEY_HERE)**
- Source the API key from groq.

### Structure

This is the project structure:

```text
draft-lifecycle-agent/
│
├── agents/
│   └── lifecycle_agent.py
│
├── tools/
│   ├── analytics_tools.py
│   ├── conversion_tools.py
│   ├── diff_engine.py
│   ├── draft_store.py
│   ├── draft_tools.py
│   ├── email_target.py
│   ├── lifecycle_tools.py
│   └── reconciliation_tool.py
│
├── data/
│   ├── drafts.json
│   └── emails.json
│
├── .env
├── main.py
├── models.py
├── target_system.py
├── requirements.txt
└── README.md
```
(Additional test files are also present, in the repo root, they are not listed in the structure here)

### Running:
- Type **python main.py** the project starts running, and requests to enter a prompt.
- Type **quit** to stop (or) **ctrl+c**
