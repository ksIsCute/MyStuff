import flask, re, os, pymongo, bcrypt, base64, string, random
from flask import Flask, render_template, make_response, request, redirect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

client = MongoClient(os.environ["dburl"], server_api=ServerApi("1"))

db = client["MyStuff"]["MainDB"]

def checkuser(user, token):
  for person in db.find(
    {
      "token": token
    }
  ):
    if person['name'].lower() == user.lower():
      return True
    else:
      return False
  

try:
  client.admin.command("ping")
except Exception as e:
  print(e)

app = Flask(__name__, "/static")

limit = Limiter(get_remote_address,
                app=app,
                default_limits=["200 per day", "50 per hour"])


@app.route("/status")
def status():
  return redirect("https://stats.uptimerobot.com/2JgmlCVB0O")

@app.route("/")
def slash():
  if request.args:
    try:
      error = request.args.get("error")
      success = request.args.get("success")
    except:
      error = None
      success = None
  else:
    error = None
    success = None
  if request.cookies:
    return render_template("/wip/index.html",
                           name=request.cookies.get("x-session-name"),
                           error=error)
  else:
    return render_template("/wip/index.html", error=error, success=success)

@app.route("/accounts/almostdelete")
def almostdelete():
  if request.cookies:
    if checkuser(request.cookies.get("x-session-name"), request.cookies.get("x-session-token")):
      if request.args:
        if request.args.get("utoken") and request.args.get("uname"):
          for user in db.find():
            if user['name'].lower() == request.args.get("uname").lower():
              if user['token'] == request.args.get("utoken"):
                if bcrypt.checkpw(request.args.get("pword").encode("UTF8"),user["password"].encode("UTF8")):
                  db.update_one({
                    "name": request.args.get("uname")
                  }, {
                    "$set": {
                      "flagged": True
                    }
                  })
                  return redirect("https://mystuff.ksiscute.repl.co/accounts/delete")
  return redirect("https://mystuff.ksiscute.repl.co/?error=Something went wrong! Didn't delete your account!")
  

@app.route("/accounts/delete")
def deleteacc():
  if request.cookies:
    if checkuser(request.cookies.get("x-session-name"), request.cookies.get("x-session-token")):
      try:
        if db.find_one({
          "name": request.cookies.get("x-session-name")
        })['flagged']:
            letters = string.ascii_letters + string.digits
            db.update_one(
              {
                "name": request.cookies.get("x-session-name")
              },
              {
                "$set": {
                  "name": f"deleted-account-{''.join(random.choice(letters) for i in range(35))}",
                  "email": None,
                  "password": None,
                  "deleted": True,
                  "settings": {
                    "dob": {
                      "year": None,
                      "month": None,
                      "day": None
                    },
                    "profile": {
                      "status": "Account has been deleted | Requested by original user.",
                      "expiry": None,
                      "bio": "",
                      "picture": {
                        "active": False,
                        "meta": None
                      },
                      "links": {}
                    }
                  }
                }
              }
            )
            resp = make_response(
                redirect(
                  "https://mystuff.ksiscute.repl.co/?success=Deleted your account!"
                ))
            resp.set_cookie('x-session-name', '', expires=0)
            resp.set_cookie('x-session-token', '', expires=0)
            return resp
      except KeyError:
        return redirect("https://mystuff.ksiscute.repl.co?error=Please delete your account through the settings menu!")
      else:
        return redirect("https://mystuff.ksiscute.repl.co/?error=Please delete your account through the settings menu!")
    else:
      resp = make_response(
          redirect(
            "https://mystuff.ksiscute.repl.co/?error=You've been signed out for your security!"
          ))
      resp.set_cookie('x-session-name', '', expires=0)
      resp.set_cookie('x-session-token', '', expires=0)
      return resp
  else:
    return redirect("https://mystuff.ksiscute.repl.co/signup?error=Please sign in!")

@app.route("/profile/@<username>")
def profiles(username):
  try:
    user = db.find_one({"name": re.compile(username, re.IGNORECASE)})
    user["name"]
  except:
    return redirect(
      "https://mystuff.ksiscute.repl.co/?error=User doesn't exist! Check for typos!"
    )
  return render_template("/wip/profile.html", name=user["name"], user=user)


@app.route("/settings", methods=["GET", "POST"])
def settings():
  if request.cookies:
    if checkuser(request.cookies.get("x-session-name"), request.cookies.get("x-session-token")):
      error = ""
      if request.method == "POST":
        for link in db.find_one({"name":request.cookies.get("x-session-name")})['settings']['profile']['links']:
          if request.form.get(f"check-{link}"):
            db.update_one(
              {
                "name": request.cookies.get("x-session-name")
              },
              {
                "$unset": {
                  f"settings.profile.links.{link}": 1
                }
              }
            )
        if request.form.get("status"):
          if len(request.form.get("status")) < 51:
            db.update_one({"name": request.cookies.get("x-session-name")}, [{
              "$set": {
                "settings": {
                  "profile": {
                    "status": request.form.get("status")
                  },
                }
              }
            }])
          else:
            error += " your status was above the 50 character limit,"
        if request.form.get("bio"):
          if len(request.form.get("bio")) < 1001:
            db.update_one({"name": request.cookies.get("x-session-name")}, [{
              "$set": {
                "settings": {
                  "profile": {
                    "bio": request.form.get("bio")
                  },
                }
              }
            }])
          else:
            error += " your bio was above the 1000 character limit!"
        if flask.request.files.get('profilephoto', ''):
          imagefile = flask.request.files.get('profilephoto', '')
          db.update_one({"name": request.cookies.get("x-session-name")}, [{
            "$set": {
              "settings": {
                "profile": {
                  "picture": {
                    "active": True,
                    "meta": base64.b64encode(imagefile.read()).decode("utf-8")
                  }
                }
              }
            }
          }])
        if request.form.get("name") and request.form.get("link"):
          if len(request.form.get("name")) < 20:
            db.update_one({"name": request.cookies.get("x-session-name")}, [{
              "$set": {
                "settings": {
                  "profile": {
                    "links": {
                      request.form.get("name"): request.form.get("link")
                    }
                  }
                }
              }
            }])
          else:
            error += " your link name was above the 20 character limit!"
    else:
      resp = make_response(
            redirect(
              "https://mystuff.ksiscute.repl.co/?error=You've been signed out for your security!"
            ))
      resp.set_cookie('x-session-name', '', expires=0)
      resp.set_cookie('x-session-token', '', expires=0)
      return resp
    return render_template(
      "/wip/settings.html",
      name=request.cookies.get("x-session-name"),
      token=request.cookies.get("x-session-token"),
      user=db.find_one({"name":re.compile(request.cookies.get("x-session-name"),re.IGNORECASE)}))
  return redirect(
      "https://mystuff.ksiscute.repl.co?error=Please login to get access to the SETTINGS menu!"
    )


  
@app.route("/browse", methods=['GET', 'POST'])
def browse():
  return render_template("/wip/browse.html", users=db.find({}).sort("_id", -1), name=request.cookies.get("x-session-name"))


@app.route("/signin", methods=["GET", "POST"])
def signin():
  if request.cookies:
    return redirect(
          "https://mystuff.ksiscute.repl.co/?error=You're already logged in!")
  if request.method == "POST":
    uid = 1
    for x in db.find():
      uid += 1
      if str(x["name"]).lower() == request.form.get("uname").lower():
        if bcrypt.checkpw(request.form.get("pword").encode("UTF8"),x["password"].encode("UTF8")):
          resp = make_response(redirect("https://mystuff.ksiscute.repl.co/settings"))
          resp.set_cookie("x-session-token",x['token'])
          resp.set_cookie("x-session-name", request.form.get("uname"))
          return resp
        else:
          return render_template(
            "/accounts/signin.html",
            error="Password and/or username is incorrect!", signing="in",
          )
    return render_template("/accounts/signin.html",
                           error="That username doesn't exist!", signing="in")

  return render_template("/accounts/signin.html", signing="in")


@app.route("/signup", methods=["GET", "POST"])
def signup():
  if request.cookies:
    return redirect("https://mystuff.ksiscute.repl.co?error=Sign out first!")
  if request.method == "POST":
    if len(request.form.get("pword")) > 50:
      return render_template(
        "/accounts/signin.html",
        error="Your password must be under 50 characters!",
        signing="up")
    if len(request.form.get("uname")) < 2 or len(
        request.form.get("uname")) > 30:
      return render_template(
        "/accounts/signin.html",
        error=
        "Your username is too long or too short! Please keep it under 30 characters, and at least over 2 characters!",
        singing="up")
    for x in db.find():
      if x["name"].lower() == request.form.get("uname").lower():
        return render_template(
          "/accounts/signin.html",
          error="That username is taken! Please try another!",
          singing="up")
    uid = 1
    try:
      for x in db.find({}):
        uid += 1
    except:
      pass
    token = bcrypt.hashpw(request.form.get("uname").encode("UTF8"), bcrypt.gensalt()).decode("UTF8")
    db.insert_one({
      "_id": uid,
      "name": request.form.get("uname"),
      "password":
      f'{bcrypt.hashpw(request.form.get("pword").encode("UTF8"), bcrypt.gensalt()).decode("UTF8")}',
      "email":
      f'{bcrypt.hashpw(request.form.get("email").encode("UTF8"), bcrypt.gensalt()).decode("UTF8")}',
      "token": token,
      "settings": {
        "dob": {
          "year": request.form.get("date").split("-")[0],
          "month": request.form.get("date").split("-")[1],
          "day": request.form.get("date").split("-")[2],
          "showing": False,
        },
        "profile": {
          "links": {},
          "bio":
          "This user has not set their bio! Encourage them to create one!",
          "status": "",
          "expiry": "N",
          "badges": ["beta"],
          "picture": {
            "active": True,
            "meta": os.environ["defaultpfp"],
          },
        },
      },
    })
    resp = make_response(redirect("https://mystuff.ksiscute.repl.co/settings"))
    resp.set_cookie("x-session-name", request.form.get("uname"))
    resp.set_cookie("x-session-token", token)
    return resp
  return render_template("/accounts/signin.html", signing="up")


@app.route("/signout")
def signout():
  if request.cookies:
    if checkuser(request.cookies.get("x-session-name"), request.cookies.get("x-session-token")):
      resp = make_response(
        redirect(
          "https://mystuff.ksiscute.repl.co/?success=Signed you out of your account!"
        ))
      resp.set_cookie('x-session-name', '', expires=0)
      resp.set_cookie('x-session-token', '', expires=0)
      return resp
    else:
      resp = make_response(
              redirect(
                "https://mystuff.ksiscute.repl.co/?error=You've been signed out for your security!"
              ))
      resp.set_cookie('x-session-name', '', expires=0)
      resp.set_cookie('x-session-token', '', expires=0)
      return resp 
  return redirect(
    "https://mystuff.ksiscute.repl.co?error=You have to sign in to sign out!")


@app.errorhandler(404)
@limit.exempt
def not_found(e):
  return render_template("404.html")


app.register_error_handler(400, not_found)
app.run("0.0.0.0", 8080)
