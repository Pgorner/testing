#!/usr/bin/env python3
import os, json, time, threading, logging, random, secrets, hmac, hashlib, base64, re
from datetime import datetime, timedelta
from flask import Flask, request, render_template, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from helpers import search_emails  # Ensure this function is defined in helpers.py
from helpers import send_confirmation_email, send_password_reset_email

BEER_VALVE_PIN = 22 
COCKTAIL_VALVE_PIN = 23  

# --- Hardware Imports ---
try:
    import RPi.GPIO as GPIO
    from hx711 import HX711
except ImportError:
    GPIO = None
    class HX711:
        def __init__(self, dout_pin, pd_sck_pin):
            self.dout_pin = dout_pin
            self.pd_sck_pin = pd_sck_pin
        def reset(self):
            pass
        def get_weight(self, times=5):
            return 0
        def power_down(self):
            pass
        def power_up(self):
            pass

# Import the HX711 scale module
import hx

# --- Logging ---
logging.basicConfig(level=logging.INFO)

# --- Flask App Setup & Config ---
app = Flask(__name__)
app.secret_key = "a3dcb4d229de6fde0db5686dee47145d"  # Use a secure key

# --- Config Persistence Helpers ---
CONFIG_FILE = "config.json"

default_admin_config = {
    "beer": {
        "price_per_ml": 0.005,   # €/ml (equivalent to 5 €/L)
        "drink_name": "Beer",
        "barrel_size": 5000,     # barrel capacity in ml
        "theoretical_weight": 0  # editable manufacturer's data
    },
    "cocktail": {
        "price_per_ml": 0.01,    # €/ml (equivalent to 10 €/L)
        "drink_name": "Cocktail",
        "container_size": 1000,  # container capacity in ml
        "theoretical_weight": 0  # editable manufacturer's data
    },
    "scale": {
        "beer_tare": 0.0,         # measured beer empty weight (g)
        "cocktail_tare": 0.0,     # measured cocktail empty weight (g)
        "current_weight": 0.0     # most recent measurement (g)
    },
    "ml_per_gram": 1.0          # conversion factor: grams to ml
}

def recursive_update(d, u):
    for k, v in u.items():
        if isinstance(v, dict):
            d[k] = recursive_update(d.get(k, {}), v)
        else:
            d.setdefault(k, v)
    return d

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            try:
                config = json.load(f)
            except Exception as e:
                logging.exception("Error loading config; using defaults")
                config = {}
    else:
        config = {}
    config = recursive_update(config, default_admin_config)
    return config

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

admin_config = load_config()

# --- User Data Functions ---
USERS_FILE = "users.json"
if os.path.exists(USERS_FILE):
    with open(USERS_FILE, "r") as f:
        try:
            users = json.load(f)
        except Exception:
            users = {}
else:
    users = {}

def save_users():
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def generate_user_id():
    while True:
        user_id = f"{random.randint(1, 999999):06d}"
        if user_id != "000000":
            return user_id

def generate_verification_token():
    return secrets.token_urlsafe(16)

def user_exists(username):
    return username in users

# Updated register_user to store a hashed password.
def register_user(username, email, first_name, last_name, password):
    if username in users:
        return None
    user_id = generate_user_id()
    token = generate_verification_token()
    users[username] = {
        "username": username,
        "email": email,
        "user_id": user_id,
        "first_name": first_name,
        "last_name": last_name,
        "password": generate_password_hash(password),
        "is_verified": False,
        "verification_token": token,
        "reset_token": None,
        # Dashboard and transaction data
        "beer_consumed": 0.0,
        "cocktails_drunk": 0.0,
        "ranking": None,
        "remaining_funds": 0.0,
        "last_transaction": 0.0,
        "transaction_history": []
    }
    save_users()
    return users[username]

def get_user(username):
    return users.get(username)

def verify_user_by_token(token):
    for username, user in users.items():
        if user.get("verification_token") == token:
            user["is_verified"] = True
            user["verification_token"] = None
            save_users()
            return user
    return None

def update_user(username, updates):
    if username in users:
        users[username].update(updates)
        save_users()
        return True
    return False

def update_user_by_id(user_id, amount):
    for username, user in users.items():
        if user.get("user_id") == user_id:
            user["remaining_funds"] += amount
            user["last_transaction"] = amount
            save_users()
            return True
    return False

def get_all_users():
    return list(users.values())

# --- Password Reset Logic ---
# For simplicity, we simulate sending an email by flashing the reset link.
@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        user = next((u for u in users.values() if u["email"] == email), None)
        if user:
            token = secrets.token_urlsafe(16)
            user["reset_token"] = token
            save_users()
            send_password_reset_email(user)  # Send actual email.
            flash("Password reset link has been sent to your email.", "info")
        else:
            flash("Email address not found.", "error")
        return redirect(url_for("forgot_password"))
    return render_template("forgot_password.html")

@app.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    # Find user by reset token.
    user = next((u for u in users.values() if u.get("reset_token") == token), None)
    if not user:
        flash("Invalid or expired password reset token.", "error")
        return redirect(url_for("login"))
    if request.method == "POST":
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        if password != confirm or not password:
            flash("Passwords do not match or are empty.", "error")
            return redirect(url_for("reset_password", token=token))
        user["password"] = generate_password_hash(password)
        user["reset_token"] = None
        save_users()
        flash("Password has been reset. Please log in.", "info")
        return redirect(url_for("login"))
    return render_template("reset_password.html", token=token)

# --- Public User Routes ---
# --- Modified Index Route ---
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        if not username:
            flash("Please enter a username.", "error")
            return redirect(url_for("index"))
        if user_exists(username):
            flash("User exists. Please log in.", "info")
            return redirect(url_for("login", username=username))
        else:
            flash("User not found. Please register.", "info")
            return redirect(url_for("register", username=username))
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username or not password:
            flash("Please enter both username and password.", "error")
            return redirect(url_for("login"))
        user = get_user(username)
        if user and check_password_hash(user.get("password", ""), password):
            session["user"] = username
            # Enforce email verification:
            if not user.get("is_verified"):
                flash("Please verify your email before proceeding.", "error")
                return redirect(url_for("profile"))
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password.", "error")
            return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username   = request.form.get("username", "").strip()
        email      = request.form.get("email", "").strip()
        first_name = request.form.get("first_name", "").strip()
        last_name  = request.form.get("last_name", "").strip()
        password   = request.form.get("password", "")
        if not username or not email or not first_name or not last_name or not password:
            flash("Please provide all required fields.", "error")
            return redirect(url_for("register"))
        if user_exists(username):
            flash("User already exists. Please log in.", "error")
            return redirect(url_for("login"))
        user = register_user(username, email, first_name, last_name, password)
        if user:
            send_confirmation_email(user)  # Now actually sends the confirmation email.
            session["user"] = username
            flash("Registration successful! A confirmation email has been sent. Please verify your email.", "info")
            return redirect(url_for("dashboard"))
        else:
            flash("An error occurred during registration.", "error")
            return redirect(url_for("register"))
    username = request.args.get("username", "")
    return render_template("register.html", username=username)

@app.route("/dashboard")
def dashboard():
    if not session.get("user"):
        return redirect(url_for("index"))
    username = session["user"]
    user = get_user(username)
    # Enforce email verification before allowing dashboard use.
    if not user.get("is_verified"):
        flash("Please verify your email before accessing the dashboard.", "error")
        return redirect(url_for("profile"))
    return render_template("dashboard.html", user=user)

@app.route("/profile")
def profile():
    if not session.get("user"):
        return redirect(url_for("index"))
    username = session["user"]
    user = get_user(username)
    return render_template("profile.html", user=user)

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("index"))

@app.route("/verify/<token>")
def verify_email(token):
    user = verify_user_by_token(token)
    if user:
        flash("Your email has been verified!", "info")
    else:
        flash("Invalid or expired verification token.", "error")
    return redirect(url_for("profile"))

# --- Pour Endpoints for Controlling the Valves & Weight Sensor ---
def open_valve(drink_type):
    if drink_type == "beer":
        GPIO.output(BEER_VALVE_PIN, GPIO.HIGH)
    elif drink_type == "cocktail":
        GPIO.output(COCKTAIL_VALVE_PIN, GPIO.HIGH)
    logging.info(f"Opened valve for {drink_type}")

def close_valve(drink_type):
    if drink_type == "beer":
        GPIO.output(BEER_VALVE_PIN, GPIO.LOW)
    elif drink_type == "cocktail":
        GPIO.output(COCKTAIL_VALVE_PIN, GPIO.LOW)
    logging.info(f"Closed valve for {drink_type}")

@app.route("/pour/start", methods=["POST"])
def pour_start():
    data = request.get_json()
    drink_type = data.get("drink_type")
    user_id = data.get("user_id")
    if drink_type not in ["beer", "cocktail"]:
        return jsonify({"error": "Invalid drink type"}), 400
    # Get starting weight (convert raw reading into grams)
    start_weight = hx.get_weight(5) / hx.CALIBRATION_FACTOR
    session["pour_start_weight"] = start_weight
    session["pour_drink_type"] = drink_type
    open_valve(drink_type)
    return jsonify({"message": f"{drink_type.capitalize()} valve opened", "start_weight": start_weight})

@app.route("/pour/stop", methods=["POST"])
def pour_stop():
    data = request.get_json()
    user_id = data.get("user_id")
    drink_type = session.get("pour_drink_type")
    if drink_type not in ["beer", "cocktail"]:
        return jsonify({"error": "Pour not properly initiated"}), 400
    start_weight = session.get("pour_start_weight")
    if start_weight is None:
        return jsonify({"error": "Pour start weight not recorded"}), 400
    # Get current weight (convert raw reading into grams)
    current_weight = hx.get_weight(5) / hx.CALIBRATION_FACTOR
    overall_baseline = admin_config["scale"]["beer_tare"] + admin_config["scale"]["cocktail_tare"]
    poured_volume = overall_baseline - current_weight
    price_per_ml = admin_config[drink_type]["price_per_ml"]
    cost = poured_volume * price_per_ml
    close_valve(drink_type)
    admin_config["scale"]["current_weight"] = current_weight
    save_config(admin_config)
    for username, user in users.items():
        if user.get("user_id") == user_id:
            user["remaining_funds"] -= cost
            user["last_transaction"] = cost
            if drink_type == "beer":
                user["beer_consumed"] += poured_volume / 1000.0
            elif drink_type == "cocktail":
                user["cocktails_drunk"] += poured_volume / 1000.0
            transaction = {
                "date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "drink": admin_config[drink_type]["drink_name"],
                "ml": poured_volume,
                "cost": cost
            }
            user.setdefault("transaction_history", []).append(transaction)
            save_users()
            break
    session.pop("pour_start_weight", None)
    session.pop("pour_drink_type", None)
    return jsonify({"message": f"{drink_type.capitalize()} pour stopped", "poured_ml": poured_volume, "cost": cost})

# --- Calibration Endpoints ---
@app.route("/admin/calibrate/beer", methods=["POST"])
def calibrate_beer():
    measured = hx.get_weight(5) / hx.CALIBRATION_FACTOR
    admin_config["scale"]["beer_empty"] = measured
    admin_config["scale"]["current_weight"] = measured
    admin_config["beer"]["connector_weight"] = measured - admin_config["beer"].get("theoretical_weight", 0)
    save_config(admin_config)
    flash(f"Beer calibrated: Empty weight = {measured:.2f} g. Connector weight = {admin_config['beer']['connector_weight']:.2f} g.", "info")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/calibrate/cocktail/start", methods=["POST"])
def calibrate_cocktail_start():
    baseline = hx.get_weight(5) / hx.CALIBRATION_FACTOR
    session["cocktail_calib_baseline"] = baseline
    flash(f"Baseline measured at {baseline:.2f} g. Now place the new empty cocktail container and click 'Finish Cocktail Calibration'.", "info")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/calibrate/cocktail/finish", methods=["POST"])
def calibrate_cocktail_finish():
    baseline = session.get("cocktail_calib_baseline")
    if baseline is None:
        flash("Please start cocktail calibration first.", "error")
        return redirect(url_for("admin_dashboard"))
    overall = hx.get_weight(5) / hx.CALIBRATION_FACTOR
    cocktail_tare = overall - admin_config["scale"]["beer_empty"]
    if cocktail_tare < 0:
        flash("Error: Calculated cocktail tare is negative. Ensure the new container is correctly placed.", "error")
    else:
        admin_config["scale"]["cocktail_empty"] = overall
        admin_config["cocktail"]["connector_weight"] = overall - admin_config["scale"]["beer_empty"] - admin_config["cocktail"].get("theoretical_weight", 0)
        admin_config["scale"]["current_weight"] = overall
        save_config(admin_config)
        flash(f"Cocktail calibrated: Measured overall weight = {overall:.2f} g. Connector weight = {admin_config['cocktail']['connector_weight']:.2f} g.", "info")
    session.pop("cocktail_calib_baseline", None)
    return redirect(url_for("admin_dashboard"))

# --- Measurement Endpoints ---
@app.route("/admin/measure/beer", methods=["POST"])
def measure_beer():
    measured = hx.get_weight(5) / hx.CALIBRATION_FACTOR
    net_liquid = measured - admin_config.get("scale", {}).get("beer_empty", 0)
    if net_liquid < 0:
        net_liquid = 0
    admin_config["beer"]["current_volume"] = net_liquid
    admin_config["beer"]["remaining"] = admin_config["beer"].get("barrel_size", 0) - net_liquid
    admin_config["scale"]["current_weight"] = measured
    save_config(admin_config)
    flash(f"Beer measured: {net_liquid:.2f} ml present; remaining capacity: {admin_config['beer']['remaining']:.2f} ml.", "info")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/measure/cocktail", methods=["POST"])
def measure_cocktail():
    measured = hx.get_weight(5) / hx.CALIBRATION_FACTOR
    net_liquid = measured - (admin_config.get("scale", {}).get("beer_empty", 0) + admin_config.get("scale", {}).get("cocktail_empty", 0) - admin_config["cocktail"].get("connector_weight", 0))
    if net_liquid < 0:
        net_liquid = 0
    admin_config["cocktail"]["current_volume"] = net_liquid
    admin_config["cocktail"]["remaining"] = admin_config["cocktail"].get("container_size", 0) - net_liquid
    admin_config["scale"]["current_weight"] = measured
    save_config(admin_config)
    flash(f"Cocktail measured: {net_liquid:.2f} ml present; remaining capacity: {admin_config['cocktail']['remaining']:.2f} ml.", "info")
    return redirect(url_for("admin_dashboard"))

# --- Solenoid Valve Test Endpoints ---
@app.route("/admin/test/valve/<drink_type>/open", methods=["POST"])
def admin_test_valve_open(drink_type):
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    if drink_type not in ["beer", "cocktail"]:
        flash("Invalid drink type for valve test", "error")
        return redirect(url_for("admin_dashboard"))
    open_valve(drink_type)
    flash(f"{drink_type.capitalize()} valve opened for test", "info")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/test/valve/<drink_type>/close", methods=["POST"])
def admin_test_valve_close(drink_type):
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    if drink_type not in ["beer", "cocktail"]:
        flash("Invalid drink type for valve test", "error")
        return redirect(url_for("admin_dashboard"))
    close_valve(drink_type)
    flash(f"{drink_type.capitalize()} valve closed for test", "info")
    return redirect(url_for("admin_dashboard"))


# --- Admin Routes ---
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "beerme234"

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid credentials", "error")
    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))

@app.route("/admin", methods=["GET", "POST"])
def admin_dashboard():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    if request.method == "POST":
        try:
            beer_price_l = float(request.form.get("beer_price", admin_config["beer"]["price_per_ml"] * 1000))
            cocktail_price_l = float(request.form.get("cocktail_price", admin_config["cocktail"]["price_per_ml"] * 1000))
            admin_config["beer"]["price_per_ml"] = beer_price_l / 1000.0
            admin_config["beer"]["drink_name"] = request.form.get("beer_name", admin_config["beer"]["drink_name"])
            admin_config["cocktail"]["price_per_ml"] = cocktail_price_l / 1000.0
            admin_config["cocktail"]["drink_name"] = request.form.get("cocktail_name", admin_config["cocktail"]["drink_name"])
            admin_config["beer"]["theoretical_weight"] = float(request.form.get("beer_theoretical", admin_config["beer"].get("theoretical_weight", 0)))
            admin_config["cocktail"]["theoretical_weight"] = float(request.form.get("cocktail_theoretical", admin_config["cocktail"].get("theoretical_weight", 0)))
            admin_config["beer"]["barrel_size"] = float(request.form.get("beer_barrel_size", admin_config["beer"].get("barrel_size", 0)))
            admin_config["cocktail"]["container_size"] = float(request.form.get("cocktail_container_size", admin_config["cocktail"].get("container_size", 0)))
            admin_config["scale"]["current_weight"] = float(request.form.get("current_weight", admin_config["scale"].get("current_weight", 0)))
        except ValueError:
            flash("Invalid numeric input.", "error")
            return redirect(url_for("admin_dashboard"))
        flash("Configuration updated", "info")
        save_config(admin_config)
    ref_param = request.args.get("ref", "").strip()
    days_param = request.args.get("days", "1")
    try:
        days = int(days_param)
    except ValueError:
        days = 1
    all_emails = search_emails(days)
    if ref_param:
        emails = [mail for mail in all_emails if mail.get("ref") == ref_param]
    else:
        emails = all_emails
    return render_template("admin_dashboard.html", ref_param=ref_param, emails=emails, config=admin_config, days=days)

@app.route("/admin/reset_scale", methods=["POST"])
def admin_reset_scale():
    hx.power_down()
    time.sleep(0.1)
    hx.power_up()
    flash("Scale reset successfully", "info")
    return redirect(url_for("admin_dashboard"))

# --- Background Funds Checker ---
def load_processed_transactions():
    if os.path.exists("funds.json"):
        with open("funds.json", "r") as f:
            try:
                return json.load(f)
            except Exception:
                return []
    return []

def save_processed_transactions(processed):
    with open("funds.json", "w") as f:
        json.dump(processed, f)

def background_fund_checker():
    processed = load_processed_transactions()
    while True:
        try:
            transactions = []  # Use search_emails() if desired.
            for trans in transactions:
                msg_id = trans.get("msg_id", "")
                user_ref = trans.get("ref", "")
                amount_str = trans.get("amount", "")
                if not msg_id or msg_id in processed or user_ref == "":
                    continue
                try:
                    amt = float(amount_str.replace(",", "."))
                except Exception:
                    continue
                user_found = None
                for user in get_all_users():
                    if user.get("user_id", "") == user_ref:
                        user_found = user
                        break
                if user_found is not None:
                    update_user_by_id(user_ref, amt)
                    processed.append(msg_id)
            save_processed_transactions(processed)
        except Exception:
            pass
        time.sleep(10)

def start_background_thread():
    thread = threading.Thread(target=background_fund_checker, daemon=True)
    thread.start()

# --- Main App Runner ---
if __name__=='__main__':
    start_background_thread()
    app.run(host="0.0.0.0", port=5000, debug=True)
