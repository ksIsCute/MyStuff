import flask, re, os, pymongo, bcrypt, base64
from flask import Flask, render_template, make_response, request, redirect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

client = MongoClient(os.environ['dburl'], server_api=ServerApi('1'))

db = client['MyStuff']['MainDB']

try:
  client.admin.command('ping')
except Exception as e:
  print(e)

app = Flask(__name__, '/static')

limit = Limiter(get_remote_address, app=app, default_limits=["200 per day", "50 per hour"])

@app.route("/")
def slash():
  if request.args:
    try:
      error = request.args.get("error")
    except:
      error = None
  else:
    error = None
  if request.cookies:
    return render_template("/wip/index.html", name=request.cookies.get("x-session-name"), error=error)
  else:
    return render_template("/wip/index.html", error=error)

@app.route("/profile/@<username>")
def profiles(username):
  try:
    user = db.find_one(
      {
        "name": re.compile(username, re.IGNORECASE)
      })
    user['name']
  except Exception as e:
    return redirect("https://mystuff.ksiscute.repl.co/?error=User doesn't exist! Check for typos!")
  return render_template("/wip/profile.html", name=user['name'], user=user)
  
@app.route("/settings", methods=["GET", "POST"])
def settings():
  notes = 0
  for x in db.find():
    notes += 1
  if request.cookies:
    if request.method == "POST":
      if request.form.get("bio"):
        if len(request.form.get("bio")) < 500:
          ubio = request.form.get("bio")
        else:
          return redirect("https://mystuff.ksiscute.repl.co/settings?error=Your bio must be under the 500 character threshold!")
      else:
        ubio = data[request.cookies.get("x-session-name")]['profile']['bio']
      if request.form.get("status"):
        if len(request.form.get("status")) < 100:
          status = request.form.get("status")
        else:
          return redirect("https://mystuff.ksiscute.repl.co/settings?error=Please keep your STATUS under the 100 character limit!")
      else:
        status = data[request.cookies.get("x-session-name")]['profile']['status']
      data.update_one(
        {
          "name": re.compile(request.cookies.get("x-session-name"), re.IGNORECASE)
        },
        {
          "$set": {
            "profile": {
              "bio": ubio,
              "status": status,
              "expiry": "N"
            }
          }
        }
      )
    return render_template("/wip/settings.html", name=request.cookies.get("x-session-name"))
  return redirect('https://mystuff.ksiscute.repl.co?error=Please login to get access to the SETTINGS menu!')

@app.route("/signin", methods=["GET", "POST"])
def login():
  if request.cookies:
    try:
      if request.cookies.get("x-session-name"):
        return redirect("https://mystuff.ksiscute.repl.co/?error=You're already logged in!")
    except:
      
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
    try:
      if request.cookies.get("x-session-name"):
        return redirect("https://mystuff.ksiscute.repl.co/?error=You're already logged in!")
    except:
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
                "badges": [
                  "beta"
                ],
                "picture": {
                  "active": True,
                  "meta": os.environ['defaultpfp']
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

@app.errorhandler(404)
@limit.exempt
def not_found(e):
  return render_template("404.html")

app.register_error_handler(400, not_found)
app.run('0.0.0.0', 8080)