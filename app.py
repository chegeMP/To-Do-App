from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
print("Loaded GROQ_API_KEY:", os.getenv("GROQ_API_KEY"))

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "default_secret_key")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"  

# Initialize with empty list or load from file if exists
def load_tasks():
    try:
        if os.path.exists('tasks.json'):
            with open('tasks.json', 'r') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Error loading tasks: {e}")
        return []

def save_tasks(tasks):
    try:
        with open('tasks.json', 'w') as f:
            json.dump(tasks, f)
    except Exception as e:
        print(f"Error saving tasks: {e}")

tasks = load_tasks()

@app.route('/')
def index():
    # Sort tasks by status (undone first) and creation time
    sorted_tasks = sorted(tasks, key=lambda x: (x.get('done', False), x.get('created_at', '')))
    return render_template('index.html', tasks=sorted_tasks)

@app.route('/add', methods=['POST'])
def add():
    task = request.form['task']
    if task:
        new_task = {
            'text': task, 
            'done': False,
            'created_at': datetime.now().isoformat(),
            'category': request.form.get('category', 'default'),
            'priority': request.form.get('priority', 'medium')
        }
        tasks.append(new_task)
        save_tasks(tasks)
        flash('Task added successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/done/<int:index>', methods=['GET', 'POST'])
def done(index):
    if 0 <= index < len(tasks):
        tasks[index]['done'] = True
        tasks[index]['completed_at'] = datetime.now().isoformat()
        save_tasks(tasks)
        flash('Task marked as complete!', 'success')
    return redirect(url_for('index'))

@app.route('/delete/<int:index>', methods=['GET', 'POST'])
def delete(index):
    if 0 <= index < len(tasks):
        del tasks[index]
        save_tasks(tasks)
        flash('Task deleted!', 'success')
    return redirect(url_for('index'))

@app.route('/edit/<int:index>', methods=['POST'])
def edit(index):
    if 0 <= index < len(tasks):
        tasks[index]['text'] = request.form.get('task-text')
        tasks[index]['category'] = request.form.get('category')
        tasks[index]['priority'] = request.form.get('priority')
        save_tasks(tasks)
        flash('Task updated!', 'success')
    return redirect(url_for('index'))

@app.route('/clear_completed', methods=['POST'])
def clear_completed():
    global tasks
    tasks = [task for task in tasks if not task.get('done', False)]
    save_tasks(tasks)
    flash('Completed tasks cleared!', 'success')
    return redirect(url_for('index'))

@app.route('/suggest', methods=['POST'])
def suggest():
    user_prompt = request.form.get('prompt', 'Suggest tasks for a productive day')
    category = request.form.get('category', '')
    
    if category:
        user_prompt += f" related to {category}"
        
    print(f"Sending request to Groq with prompt: {user_prompt}")

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "llama3-8b-8192",
        "messages": [
            {
                "role": "system",
                "content": "You are a productivity assistant that helps users by suggesting a useful to-do list based on a prompt. Format your response as a list of tasks, one per line, starting with a dash or number."
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        "temperature": 0.7
    }

    try:
        response = requests.post(
            GROQ_ENDPOINT,
            headers=headers,
            json=data
        )
        response.raise_for_status()
        result = response.json()
        print("Groq raw response:", result)

        message_content = result["choices"][0]["message"]["content"]

        # Split suggestions into tasks
        added_count = 0
        for line in message_content.split("\n"):
            task = line.strip("-•1234567890. ").strip()
            if task and len(task) > 3:  # Avoid empty or very short tasks
                new_task = {
                    'text': task, 
                    'done': False,
                    'created_at': datetime.now().isoformat(),
                    'category': category or 'AI Suggested',
                    'priority': 'medium'
                }
                tasks.append(new_task)
                added_count += 1

        save_tasks(tasks)
        flash(f'Added {added_count} suggested tasks!', 'success')

    except requests.exceptions.RequestException as e:
        print("Groq API error:", e)
        if hasattr(e, 'response') and e.response is not None:
            print("Error details:", e.response.text)
        flash('Failed to get task suggestions. Please try again.', 'error')

    return redirect(url_for('index'))

@app.route('/api/tasks', methods=['GET'])
def api_tasks():
    return jsonify(tasks)

if __name__ == "__main__":
    print("Server is running... Visit http://127.0.0.1:5000 in your browser")
    app.run(debug=True)