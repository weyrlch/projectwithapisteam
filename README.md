# SteamProfileInsights

A simple web app that fetches and displays Steam profile information, badges, and XP using the Steam Web API.

## 🚀 Features

- View public Steam profile data by SteamID
- Check user level and badge breakdown
- Error page for invalid or private profiles

## 🛠️ Tech Stack

- Python 3
- Flask
- Jinja2 Templates
- HTML + CSS

## 📁 Project Structure
project/
├── static/
│ └── styles.css
├── templates/
│ ├── index.html
│ ├── profile.html
│ └── error.html
├── app.py
├── api.py
├── steam_api.py
├── badge_utils.py
├── requirements.txt
└── .gitignore


## ⚙️ Installation

```bash
git clone https://github.com/weyrlch/projectwithapisteam.git
cd projectwithapisteam
python -m venv venv
source venv/bin/activate   # ou .\venv\Scripts\activate no Windows
pip install -r requirements.txt
python app.py
