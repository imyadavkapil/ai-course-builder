from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_dance.contrib.google import make_google_blueprint, google
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
import os
from dotenv import load_dotenv
from openai import OpenAI
from markdown import markdown

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecret")  # Needed for session

# Configure Google OAuth
google_bp = make_google_blueprint(
    client_id=os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"),
    scope=["profile", "email"],
    redirect_url="/login/google/authorized"
)
app.register_blueprint(google_bp, url_prefix="/login")

# Login Manager setup
login_manager = LoginManager(app)
login_manager.login_view = "google.login"

# Simple user class
class User(UserMixin):
    def __init__(self, id_, name, email):
        self.id = id_
        self.name = name
        self.email = email

# In-memory user store
users = {}

@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)

# OpenAI client (Groq)
client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

@app.route("/")
def home():
    if not current_user.is_authenticated:
        return redirect(url_for("google.login"))
    return render_template("index.html", user=current_user)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))

@app.route("/login/google/authorized")
def google_authorized():
    if not google.authorized:
        return redirect(url_for("google.login"))

    resp = google.get("/oauth2/v2/userinfo")
    assert resp.ok, resp.text
    user_info = resp.json()

    # Create user object
    user_id = user_info["id"]
    user = User(user_id, user_info["name"], user_info["email"])
    users[user_id] = user
    login_user(user)

    return redirect(url_for("home"))

@app.route("/generate", methods=["POST"])
@login_required
def generate():
    prompt = request.form.get("prompt")
    print("Prompt received:", prompt)

    system_prompt = f"You are a course creator AI. Create a full course outline based on this prompt: '{prompt}'. Include course title, 3–5 modules, and 2–3 lessons per module."

    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "system", "content": system_prompt}],
            temperature=0.7
        )

        output = response.choices[0].message.content
        html_output = markdown(output)
        return jsonify({"result": html_output})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
