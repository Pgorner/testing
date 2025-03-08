import random
import secrets
import json
import os

# File to store user data.
USERS_FILE = "users.json"

# Load users from the file (or initialize an empty dict if file not found).
if os.path.exists(USERS_FILE):
    with open(USERS_FILE, "r") as f:
        try:
            users = json.load(f)
        except Exception:
            users = {}
else:
    users = {}

def save_users():
    """Save the users dictionary to the JSON file."""
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def generate_user_id():
    """Generate a random 6-digit number as a string, not equal to '000000'."""
    while True:
        user_id = f"{random.randint(1, 999999):06d}"
        if user_id != "000000":
            return user_id

def generate_verification_token():
    """Generate a secure random token."""
    return secrets.token_urlsafe(16)

def user_exists(username):
    return username in users

def register_user(username, email, first_name, last_name):
    """
    Registers a new user with a unique username.
    A verification token is generated and the user is marked as not verified.
    Returns the user dict if successful; otherwise returns None.
    """
    if username in users:
        return None
    user_id = generate_user_id()
    token = generate_verification_token()
    # You can add additional fields as needed.
    users[username] = {
        "username": username,
        "email": email,
        "user_id": user_id,
        "first_name": first_name,
        "last_name": last_name,
        "is_verified": False,
        "verification_token": token,
        # Additional fields for your dashboard
        "beer_consumed": 0,       # e.g., in Liters
        "cocktails_drunk": 0,
        "ranking": None,          # e.g., numeric rank or string "5th"
        "remaining_funds": 0.0,    # e.g., account balance
        "last_transaction": 0.0    # e.g., last transaction amount
    }
    save_users()
    return users[username]

def get_user(username):
    return users.get(username)

def verify_user_by_token(token):
    """
    Searches for a user with the given verification token.
    If found, marks the user as verified and returns the user.
    Otherwise returns None.
    """
    for username, user in users.items():
        if user.get("verification_token") == token:
            user["is_verified"] = True
            # Optionally clear the token after verification.
            user["verification_token"] = None
            save_users()
            return user
    return None

def update_user(username, updates):
    """
    Update the user's data with the provided dictionary.
    """
    if username in users:
        users[username].update(updates)
        save_users()
        return True
    return False

def update_user_by_id(user_id, amount):
    """
    Find the user with the given user_id and update their funds:
      - Increase 'remaining_funds' by amount.
      - Set 'last_transaction' to amount.
    Returns True if updated, False if no matching user found.
    """
    for username, user in users.items():
        if user.get("user_id") == user_id:
            # Update the funds and last transaction.
            user["remaining_funds"] += amount
            user["last_transaction"] = amount
            save_users()
            return True
    return False

def get_all_users():
    """
    Return a list of all user dictionaries.
    """
    return list(users.values())
