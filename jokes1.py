from flask import Flask, jsonify
import requests
import sqlite3

app = Flask(__name__)

# Database setup
DB_NAME = "jokes.db"

def create_table():
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Drop table if it exists
    cursor.execute("DROP TABLE IF EXISTS jokes")

    cursor.execute('''
        CREATE TABLE jokes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            type TEXT,
            joke TEXT,
            setup TEXT,
            delivery TEXT,
            nsfw BOOLEAN,
            political BOOLEAN,
            sexist BOOLEAN,
            safe BOOLEAN,
            lang TEXT
        )
    ''')
    conn.commit()
    conn.close()

def fetch_jokes(total_jokes=100, batch_size=10):
    """Fetches jokes from JokeAPI until reaching total_jokes."""
    url = "https://v2.jokeapi.dev/joke/Any?amount=10"
    jokes = []

    while len(jokes) < total_jokes:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if "jokes" in data:
                jokes.extend(data["jokes"])
        else:
            print(f"Failed to fetch jokes: {response.status_code}")
    
    return jokes[:total_jokes]  # Ensure we return exactly 100

def process_and_store_jokes():
    """Fetch, process, and store jokes in SQLite."""
    jokes = fetch_jokes()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    for joke in jokes:
        category = joke.get("category", "")
        joke_type = joke.get("type", "")
        nsfw = joke["flags"].get("nsfw", False)
        political = joke["flags"].get("political", False)
        sexist = joke["flags"].get("sexist", False)
        safe = joke.get("safe", False)
        lang = joke.get("lang", "")

        # Handle "single" and "twopart" joke types
        if joke_type == "single":
            joke_text = joke.get("joke", "")
            setup, delivery = None, None
        else:
            joke_text = None
            setup = joke.get("setup", "")
            delivery = joke.get("delivery", "")

        # Insert into database
        cursor.execute('''
            INSERT INTO jokes (category, type, joke, setup, delivery, nsfw, political, sexist, safe, lang)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (category, joke_type, joke_text, setup, delivery, nsfw, political, sexist, safe, lang))

    conn.commit()
    conn.close()
    return {"message": f"{len(jokes)} jokes stored successfully"}

@app.route('/fetch_jokes', methods=['GET'])
def fetch_and_store():
    """API endpoint to fetch and store jokes."""
    result = process_and_store_jokes()
    return jsonify(result)

if __name__ == '__main__':
    create_table()  
    app.run(debug=True)

