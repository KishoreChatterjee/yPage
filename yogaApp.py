# Import the Flask module
from flask import Flask, render_template, flash
from flask import Flask, request, jsonify
import json
import bcrypt
from bcrypt import checkpw
import requests


# Create a Flask application instance
app = Flask(__name__)
app.secret_key = 'mysecretkey'

def load_user_data():
    try:
        with open("custom_users.json") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"user": []}
    

def hash_password(password):
    # Hash the password using bcrypt
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed_password.decode('utf-8')    
    

# Define a route for the home page
@app.route('/')
def home():
    # Render the home page template
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        # Load user data from JSON file
        users = load_user_data()

        # Check if user with provided email exists
        for user in users["user"]:
            if user["email"] == email:
                # Check if provided password matches hashed password
                if checkpw(password.encode('utf-8'), user["password"].encode('utf-8')):
                    flash("Logged in successfully!", "success")
                    return render_template("dashboard.html")
                else:
                    flash("Invalid email or password", "danger")
                    return render_template("login.html")

        # If user with provided email doesn't exist, show error message
        flash("Invalid email or password", "danger")
        return render_template("login.html")
    else:
        return render_template("login.html")

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == "POST":
        full_name = request.form["full_name"]
        username = request.form["username"]
        email = request.form["email"]
        phone_number = request.form["phone_number"]
        gender = request.form["gender"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if len(full_name) == 0 or len(username) == 0 or len(email) == 0 or len(phone_number) == 0 or len(gender) == 0 or len(password) == 0 or len(confirm_password) == 0:
            flash("Please fill in all fields", "warning")
            return render_template("signup.html")
        elif password != confirm_password:
            flash("Passwords do not match", "warning")
            return render_template("signup.html")
        else:
            try:
                with open("custom_users.json") as f:
                    data = json.load(f)
            except FileNotFoundError:
                data = {"user": []}

            for user in data["user"]:
                if user["email"] == email:
                    flash("User already exists", "warning")
                    return render_template("signup.html")
                
            # Hash the password before storing it
            hashed_password = hash_password(password)    

            new_user = {
                "full_name": full_name,
                "username": username,
                "email": email,
                "phone_number": phone_number,
                "gender": gender,
                "password": hashed_password
            }
            data["user"].append(new_user)

            with open("custom_users.json", "w") as f:
                json.dump(data, f, indent=4)

            flash("Account created successfully!", "success")
            return render_template("home.html")

    else:
        return render_template("signup.html")


@app.route('/get_bot_response', methods=['POST'])
def get_bot_response():
    try:
        # Get user message from the JSON data
        user_message = request.json.get('user_message')
        if not user_message:
            return jsonify({'error': 'User message not provided'}), 400

        # Send user message to Rasa server
        rasa_response = requests.post('http://localhost:5005/webhooks/rest/webhook', json={'message': user_message})

        # Debug: print the response from Rasa
        print(f"Rasa response status code: {rasa_response.status_code}")
        print(f"Rasa response JSON: {rasa_response.json()}")

        # Check if Rasa server responded successfully
        if rasa_response.status_code == 200:
            response_data = rasa_response.json()
            if response_data:
                bot_response = response_data[0].get('text', "Sorry, I couldn't understand that.")
            else:
                bot_response = "Sorry, I couldn't understand that."
        else:
            bot_response = "Sorry, I couldn't understand that."

        # Return bot response
        return jsonify({'bot_response': bot_response}), 200
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Failed to connect to Rasa server'}), 500
    except Exception as e:
        # Log the exception if needed
        print(f"An error occurred: {e}")
        return jsonify({'error': str(e)}), 500

# Run the Flask application
if __name__ == '__main__':
    app.run(debug=True)
