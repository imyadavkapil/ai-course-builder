import os
from flask import Flask, render_template, request, jsonify
from openai import OpenAI
from markdown import markdown
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecret")

# OpenAI client (Groq or OpenAI compatible)
client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    prompt = request.form.get("prompt")
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


@app.route("/clear")
def clear_session():
    return "Session cleared. <a href='/'>Go home</a>"


if __name__ == "__main__":
    app.run(debug=True)
