## channel.py - a simple message channel
##

from flask import Flask, request, render_template, jsonify
import json
import requests
import datetime
import random

# Class-based application configuration
class ConfigClass(object):
    """ Flask application config """

    # Flask settings
    SECRET_KEY = 'This is an INSECURE secret!! DO NOT use this in production!!'

# Create Flask app
app = Flask(__name__)
app.config.from_object(__name__ + '.ConfigClass')  # configuration
app.app_context().push()  # create an app context before initializing db

HUB_URL = 'https://temporary-server.de'
HUB_AUTHKEY = 'Crr-K3d-2N'
CHANNEL_AUTHKEY = '0987654321'
CHANNEL_NAME = "Feeling Lucky?"
CHANNEL_ENDPOINT = "http://vm150.rz.uni-osnabrueck.de/user087/channel.wsgi" # don't forget to adjust in the bottom of the file
CHANNEL_FILE = 'messages.json'
SECRET_NUMBER = 0
START = True

@app.cli.command('register')
def register_command():
    global CHANNEL_AUTHKEY, CHANNEL_NAME, CHANNEL_ENDPOINT

    # send a POST request to server /channels
    response = requests.post(HUB_URL + '/channels', headers={'Authorization': 'authkey ' + HUB_AUTHKEY},
                             data=json.dumps({
            "name": CHANNEL_NAME,
            "endpoint": CHANNEL_ENDPOINT,
            "authkey": CHANNEL_AUTHKEY}))

    if response.status_code != 200:
        print("Error creating channel: "+str(response.status_code))
        return

def check_authorization(request):
    global CHANNEL_AUTHKEY
    # check if Authorization header is present
    if 'Authorization' not in request.headers:
        return False
    # check if authorization header is valid
    if request.headers['Authorization'] != 'authkey ' + CHANNEL_AUTHKEY:
        return False
    return True

@app.route('/health', methods=['GET'])
def health_check():
    global CHANNEL_NAME
    if not check_authorization(request):
        return "Invalid authorization", 400
    return jsonify({'name':CHANNEL_NAME}),  200

# GET: Return list of messages
@app.route('/', methods=['GET'])
def home_page():
    if not check_authorization(request):
        return "Invalid authorization", 400
    # fetch channels from server
    read_message = read_messages()
    return jsonify(read_message)

# POST: Send a message
@app.route('/', methods=['POST'])
def send_message():
    # fetch channels from server
    # check authorization header
    if not check_authorization(request):
        return "Invalid authorization", 400
    # check if message is present
    message = request.json
    if not message:
        return "No message", 400
    if not 'content' in message:
        return "No content", 400
    if not 'sender' in message:
        return "No sender", 400
    if not 'timestamp' in message:
        return "No timestamp", 400
    # add message to messages
    messages = read_messages()
    messages.append({'content':message['content'], 'sender':message['sender'], 'timestamp':message['timestamp']})
    reply = game_bot_reply(message)
    messages.append(reply)
    save_messages(messages)
    return "OK", 200

def read_messages():
    global CHANNEL_FILE
    messages = []
    try:
        f = open(CHANNEL_FILE, 'r')
    except FileNotFoundError:
        return []
    try:
        messages = json.load(f)   
    except json.decoder.JSONDecodeError as e:
        if not messages:
            message_content = "Welcome to the Number Guessing Game! Choose your difficulty: (easy, medium, hard): "
            message_sender = "royal_flusher"
            message_timestamp = datetime.datetime.now().isoformat()
            messages.append({'content':message_content, 'sender':message_sender, 'timestamp':message_timestamp})
            START = True
        else:
            messages = []
            print(e)
    f.close()
    return messages

def save_messages(messages):
    global CHANNEL_FILE
    with open(CHANNEL_FILE, 'w') as f:
        json.dump(messages, f)

def select_difficulty(difficulty):
    # Set secret number based on difficulty
    if difficulty == "easy":
        min_range, max_range = 1, 20
    elif difficulty == "medium":
        min_range, max_range = 1, 50
    else:
        min_range, max_range = 1, 100
    sec_number = random.randint(min_range, max_range)
    return sec_number

def game_bot_reply(message):
    global SECRET_NUMBER
    global START
    content = message['content'] 
    sender = message['sender']
    
    if START:
        if content in ['easy', 'medium', 'hard']:
            SECRET_NUMBER = select_difficulty(content)
            print(SECRET_NUMBER)
            reply_content = "Guess the number now!"
            START = False
        else:
            reply_content = "It seems you didn't choose appropriate difficulty. Please try again."
    else:
        # Check guess and provide feedback
        try:
            numbers = [int(word) for word in content.split() if word.isdigit()]
            if numbers:
                guess = numbers[0]  # Take the first number
                if guess == SECRET_NUMBER:
                    reply_content = "Congratulations " + sender +"! You guessed the number! \n Let's play again, choose your difficulty: (easy, medium, hard): "
                    START = True
                elif guess < SECRET_NUMBER:
                    reply_content = sender + " your guess is too low. Try again."
                else:
                    reply_content = sender + " your guess is too high. Try again."
            else:
                reply_content = "It seems you didn't mention any numbers. Please try again."
        except ValueError:
            reply_content = "Sorry, I only understand numbers for guessing! "

    reply_sender = "royal_flusher"
    reply_timestamp = datetime.datetime.now().isoformat()
    reply = {'content':reply_content, 'sender':reply_sender, 'timestamp':reply_timestamp}
    return reply

# Start development web server
if __name__ == '__main__':
    app.run(port=5001, debug=True)
