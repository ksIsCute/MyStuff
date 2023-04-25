import flask, os, pymongo, bcrypt, base64
from flask import Flask, render_template, make_response, request, redirect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

client = MongoClient(os.environ['dburl'], server_api=ServerApi('1'))

db = client['MyStuff']['MainDB']

try:
  client.admin.command('ping')
  print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
  print(e)

app = Flask(__name__, '/static')

limit = Limiter(get_remote_address, app=app, default_limits=["200 per day", "50 per hour"])

#<img src="data:image/jpeg;base64,' + data_base64 + '">
@app.route("/test")
def createadminportalthing():
  return "unused (for now)"

@app.route("/")
def slash():
  return render_template("index.html")

@app.route("/getstarted")
def getstarted():
  return render_template("getstarted.html")

@app.route("/signin", methods=["GET", "POST"])
def login():
  resp = make_response(redirect("https://mystuff.ksiscute.repl.co/settings"))
  if request.method == "POST":
    uid = 1
    for x in db.find():
      uid += 1
      if str(x['name']).lower() == request.form.get("uname").lower():
        if bcrypt.checkpw(request.form.get("pword").encode("UTF8"), x['password'].encode("UTF8")):
          resp.set_cookie('x-session-token', f'{bcrypt.hashpw(request.form.get("uname").encode("UTF8"), bcrypt.gensalt()).decode("UTF8")}')
          resp.set_cookie('x-session-name', request.form.get("uname"))
          return resp
        return render_template("/accounts/signin.html", error="Password and/or username is incorrect!")
    return render_template("/accounts/signin.html", error="That username doesn't exist!")
          
  return render_template("/accounts/signin.html")

@app.route("/signup", methods=["POST", "GET"])
def signup():
  if request.method == "POST":
    if len(request.form.get("pword")) > 50:
      return render_template("/accounts/signin.html", error="Your password must be under 50 characters!")
    if len(request.form.get("uname")) < 2 or len(request.form.get("uname")) > 30:
      return render_template("/accounts/signin.html", error="Your username is too long or too short! Please keep it under 30 characters, and at least over 2 characters!", singing="up")
    for x in data.find():
      if x['username'].lower() == request.form.get("uname").lower():
        return render_template("/accounts/signin.html", error="That username is taken! Please try another!", singing="up")
    uid = 1
    for x in db.find({}):
      uid += 1
    db.insert_one(
      {
        "_id":uid, 
        "name": request.form.get("uname"), 
        "password": f'{bcrypt.hashpw(request.form.get("pword").encode("UTF8"), bcrypt.gensalt()).decode("UTF8")}', 
        "email":request.form.get("email"), 
        "settings": {
          "dob":{
            "year": request.form.get("date").split("-")[0],
            "month": request.form.get("date").split("-")[1],
            "day": request.form.get("date").split("-")[2],
            "showing": False
          },
          "profile":{
            "bio": "This user has not set their bio! Encourage them to create one!",
            "status": "",
            "expiry": "N",
            "badges": [],
            "picture": {
              "active": False,
              "meta": None
            }
          }
        }
      }
    )
    resp = make_response(redirect("https://mystuff.ksiscute.repl.co/settings"))
    resp.set_cookie("x-session-name", request.form.get("uname"))
    resp.set_cookie('x-session-token', f'{bcrypt.hashpw(request.form.get("uname").encode("UTF8"), bcrypt.gensalt()).decode("UTF8")}')
    resp.headers['Content-type'] = "text/html"
    return resp
  return render_template("/accounts/signin.html", signing="up")

@app.route("/settings", methods=['POST', 'GET'])
def settings():
  if request.method == "POST":
    try:
      if request.form.get("uname") < 2:
        name = request.cookies.get("x-session-name")
      else:
        name = request.form.get("uname")
    db.update_one(
      {
        "name": request.cookies.get("x-session-name")
      },
      {
        "name": name
      }
    )
  if request.cookies:
    print(request.cookies.get("x-session-name"))
    return render_template("/accounts/settings.html", name=request.cookies.get("x-session-name"), dob=db.find_one({"name":request.cookies.get('x-session-name')})['settings']['dob'])
  return "You must sign in to access this page!"

@app.errorhandler(404)
@limit.exempt
def not_found(e):
  return render_template("404.html")

app.register_error_handler(400, not_found)
app.run('0.0.0.0', 8080)