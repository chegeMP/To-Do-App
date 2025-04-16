from flask import Flask, render_template, request, redirect, url_for
import os
import requests
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

GROK_API_KEY = os.getenv("GROK_API_KEY")
GROK_ENDPOINT = "https://api.grok.com/chat"  

tasks = []

@app.route('/')
def index():
    return render_template('index.html', tasks=tasks)

@app.route('/add', methods=['POST'])
def add():
    task = request.form['task']
    if task:
        tasks.append({'text': task, 'done': False})
    return redirect(url_for('index'))

@app.route('/done/<int:index>')
def done(index):
    tasks[index]['done'] = True
    return redirect(url_for('index'))

@app.route('/suggest', methods=['POST'])
def suggest():
    user_prompt = request.form.get('prompt', 'Suggest tasks for a productive day')

    headers = {
        "Authorization": f"Bearer {GROK_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "prompt": user_prompt,
        "max_tokens": 100,
    }

    try:
        response = requests.post(GROK_ENDPOINT, json=data, headers=headers)
        suggestions = response.json().get("suggestions", [])

        for suggestion in suggestions:
            tasks.append({'text': suggestion, 'done': False})
    except Exception as e:
        print("Grok API error:", e)

    return redirect(url_for('index'))

if __name__ == "__main__":
    print("Server is running... Visit http://127.0.0.1:5000 in your browser")
    app.run(debug=True)
