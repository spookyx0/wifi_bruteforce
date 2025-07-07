from flask import Flask, render_template, request, redirect
import random
import string

app = Flask(__name__)

valid_user = "admin"
valid_pass = "admin123"

def generate_token(length=20):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

@app.route("/")
def home():
    return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():
    csrf_token = generate_token()
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        captcha = request.form.get("captcha")

        if captcha.lower() != "abcd":
            return "Invalid CAPTCHA"
        if username == valid_user and password == valid_pass:
            return "Welcome!"
        return "Invalid credentials"

    return render_template("login.html", csrf_token=csrf_token)

if __name__ == "__main__":
    app.run(debug=True)
