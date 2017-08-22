import os
import re
from cs50 import SQL
from flask import Flask,jsonify, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import mkdtemp
from helper import *
from flask_jsglue import JSGlue
from flask_googlemaps import GoogleMaps
from flask_googlemaps import Map,icons
from flask_sslify import SSLify



import sqlite3

# configure CS50 Library to use SQLite database
db = SQL("sqlite:///finalProject.db")
app = Flask(__name__)
JSGlue(app)
sslify = SSLify(app)

app.debug = False
app.config['GOOGLEMAPS_KEY'] = "AIzaSyDBdx6qvo0OIZcnKakRkalFVot1mIaa0ts"

# Initialize the extension
GoogleMaps(app)

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.route('/')
def index():
    if session:
        notify = db.execute('SELECT * from notification WHERE user_id = :uid AND status = "unread"',uid=session["user_id"])
        history = db.execute('SELECT * from notification WHERE user_id = :uid AND status = "read" ORDER BY id DESC',uid=session["user_id"])
        if notify:
            count = db.execute("SELECT COUNT(*) FROM (SELECT * from notification WHERE user_id = :uid AND status = 'unread') alias",uid=session["user_id"])
            return render_template('index.html',notifications = notify,number=count[0]["COUNT(*)"],history=history, _external=True, _scheme='https')
        return render_template('index.html',history=history, _external=True, _scheme='https')
    return render_template('index.html', _external=True, _scheme='https')
    
@app.route('/admin',methods=['GET','POST'])
def admin():
    approve = None
    name = request.form.get("name")
    results = None
    if request.method == 'POST':
        if request.form["btn"] == "Calculate the Place":
            lat = float(request.form.get('lat'))
            lon = float(request.form.get('long'))
            results = Geocoder.reverse_geocode(lat,lon)
            approve = db.execute('SELECT * FROM admin')
            return render_template('admin.html',rows=approve,results=results, _external=True, _scheme='https')
            
        elif request.form["btn"] == "Add To Database":
            name = request.form.get("name")
            m_image = request.form.get("m_image")
            f_image = request.form.get("f_image")
            q_id = request.form.get("q_id")
            uId = request.form.get("user")
            notify = db.execute("INSERT INTO notification (user_id,message,type) VALUES(:uid,:m,'database')",uid=uId,m="Hey! We have added " + name + " into our database. Now you can track it. Thanks again for your contribution.")
            exe = db.execute("INSERT INTO birds (name,male_image,female_image) VALUES(:name,:m,:f)",name=name,m=m_image,f=f_image)
            if exe:
                db.execute("DELETE FROM admin WHERE id = :id",id=q_id)
                approve = db.execute('SELECT * FROM admin')
            return render_template('admin.html',rows=approve, _external=True, _scheme='https')
                
        elif request.form["btn"] == "Delete Request":
            q_id = request.form.get("q_id")
            db.execute("DELETE FROM admin WHERE id = :id",id=q_id)
            approve = db.execute('SELECT * FROM admin')
            return render_template('admin.html',rows=approve, _external=True, _scheme='https')
            
        elif request.form["btn"] == "Add TO Tracker":
            name = request.form.get("name")
            lat = float(request.form.get('lat'))
            lon = float(request.form.get('long'))
            m_image = request.form.get("male_image")
            f_image = request.form.get("female_image")
            catagory = request.form.get('catagory')
            uId = request.form.get("user")
            
            rows = db.execute('SELECT * FROM tracks WHERE name = :name',name=name)
            notify = db.execute("INSERT INTO notification (user_id,message,type) VALUES(:uid,:m,'track')",uid=uId,m="Hey! We have added " + name + " into the tracker. Thanks again for your contribution.")
            if rows:
                for row in rows:
                    if getDistanceFromLatLonInKm(lat,lon,row["lat"],row["long"]) < 5:
                        db.execute('UPDATE tracks SET seen = seen + 1 WHERE id = :id',id=row['id'])
                        flash('Thankyou for your contribution')
                        q_id = request.form.get("q_id")
                        db.execute("DELETE FROM admin WHERE id = :id",id=q_id)
                        approve = db.execute('SELECT * FROM admin')
                        return render_template('admin.html',rows=approve,results=results, _external=True, _scheme='https')
                
                db.execute('INSERT INTO tracks (name,lat,long,seen,catagory,male_image,female_image) VALUES(:n,:lat,:lon,1,:cat,:m,:f)',n=name,lat=lat,lon=lon,cat=catagory,m=m_image,f=f_image)
                q_id = request.form.get("q_id")
                db.execute("DELETE FROM admin WHERE id = :id",id=q_id)
                approve = db.execute('SELECT * FROM admin')
                return render_template('admin.html',rows=approve,results=results, _external=True, _scheme='https')
            else:
                db.execute('INSERT INTO tracks (name,lat,long,seen,catagory,male_image,female_image) VALUES(:n,:lat,:lon,1,:cat,:m,:f)',n=name,lat=lat,lon=lon,cat=catagory,m=m_image,f=f_image)
                q_id = request.form.get("q_id")
                db.execute("DELETE FROM admin WHERE id = :id",id=q_id)
                approve = db.execute('SELECT * FROM admin')
                return render_template('admin.html',rows=approve,results=results, _external=True, _scheme='https')
    else:
        approve = db.execute('SELECT * FROM admin')
        return render_template('admin.html',rows=approve, _external=True, _scheme='https')
    
@app.route('/contribute',methods=['GET','POST'])
@login_required
def contribute():
        result = db.execute('SELECT * FROM birds')
        row = db.execute('SELECT * FROM users WHERE id = :uid',uid=session["user_id"])
        birds = request.form.get("bird")
        if birds:
            birds_tmp = '%'+birds+'%'
            resends = db.execute("SELECT * FROM birds WHERE name LIKE :birds",birds=birds_tmp)
            if resends:
                return render_template("contribute.html",resends=resends,rows=result,username=session["user_id"], _external=True, _scheme='https')
            else:
                query = db.execute("INSERT INTO admin (name,type,userId) VALUES(:name,'add',:uid)",name=birds,uid=session["user_id"])
                flash("Oops! We didn't find any similar result, We have registered your query, we will notify you")
                return redirect(url_for("contribute", _external=True, _scheme='https'))
        else:
            history = db.execute('SELECT * from notification WHERE user_id = :uid AND status = "read" ORDER BY id DESC',uid=session["user_id"])
            return render_template("contribute.html",rows=result,username=session["user_id"],history=history, _external=True, _scheme='https')
        
@app.route('/about')
@login_required
def about():
    history = db.execute('SELECT * from notification WHERE user_id = :uid AND status = "read" ORDER BY id DESC',uid=session["user_id"])
    return render_template('about.html',history=history, _external=True, _scheme='https')
    
@app.route('/track',methods=['POST','GET'])
@login_required
def track():
    if request.method == 'POST':
        name = request.form.get("bird_name")
        m_img = request.form.get("male_image")
        f_img = request.form.get("female_image")
        username = request.form.get("username")
        lat = float(request.form.get("lat"))
        lon = float(request.form.get("lon"))
        known = db.execute('SELECT * FROM birds WHERE name = :name',name=name)
        if known: 
                db.execute('INSERT into admin (name,type,male_image,female_image,lat,long,userId) VALUES(:name,"track",:m,:f,:lat,:lon,:uname)',name=name,m=m_img,f=f_img,lat=lat,lon=lon,uname=username)
                flash('Thankyou for your contribution')
                return redirect(url_for('index', _external=True, _scheme='https'))
        else:
            query = db.execute("UPDATE admin set lat = :lat, long = :lon WHERE name = :name",lat=lat,lon=lon,name=name)        
            flash('Thankyou for your contribution')
            return redirect(url_for('index', _external=True, _scheme='https'))

@app.route('/register/',methods=["GET","POST"])
def register():
    if request.method == "POST":
        if request.form.get("password") != request.form.get("confirmation"):
            flash('Password and Confirmation didn\'t match')
            return render_template('register.html', _external=True, _scheme='https')
        crypt = pwd_context.hash(request.form.get("password"))
        check = db.execute("SELECT email FROM users WHERE email = :email",email=request.form.get("email"))
        if check:
            flash("Sorry but this email address is already registered")
            return redirect(url_for("register", _external=True, _scheme='https'))
        result = db.execute('INSERT INTO users (name,email,password,security_question) VALUES (:name,:email,:password,:q)',name=request.form.get("uname"),email=request.form.get("email"),password=crypt,q=request.form.get("question"))
        if not result:
            flash("error in insert operation")
            return redirect(url_for("register", _external=True, _scheme='https'))
        session["user_id"] = result
        flash("Registered successfully!")
        return redirect(url_for('index', _external=True, _scheme='https'))
    else:
        return render_template('register.html', _external=True, _scheme='https')


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # ensure username was submitted
        if not request.form.get("email"):
            flash("Must provide Email")
            return redirect(url_for('login', _external=True, _scheme='https'))

        # ensure password was submitted
        elif not request.form.get("password"):
            flash("Must provide password")
            return redirect(url_for('login', _external=True, _scheme='https'))
            
        if request.form.get('email') == 'admin@gmail.com' and request.form.get("password") == 'iamnarenbakshi':
            session["user_id"] = '007'
            flash("Welcome Admin!")
            return redirect(url_for('admin', _external=True, _scheme='https'))

        # query database for username
        rows = db.execute("SELECT * FROM users WHERE email = :email",email=request.form.get("email"))

        encrypted = (request.form.get("password"))
        
        
        # ensure username exists and password is correct
        if not rows:
            flash("Email not registered")
            return redirect(url_for("login", _external=True, _scheme='https'))
        elif not pwd_context.verify(encrypted,rows[0]["password"]):
            flash("Invalid password")
            return redirect(url_for('login', _external=True, _scheme='https'))

        # remember which user has logged in
        session["user_id"] = rows[0]["id"]
        # redirect user to home page
        flash("Logged In successfully!")
        notify = db.execute('SELECT * from notification WHERE user_id = :uid AND status = "unread"',uid=session["user_id"])
        history = db.execute('SELECT * from notification WHERE user_id = :uid AND status = "read" ORDER BY id DESC',uid=session["user_id"])
        if notify:
            count = db.execute("SELECT COUNT(*) FROM (SELECT * from notification WHERE user_id = :uid AND status = 'unread') alias",uid=session["user_id"])
            return render_template('index.html',notifications = notify,number=count[0]["COUNT(*)"],history=history, _external=True, _scheme='https')
        return render_template('index.html',history=history, _external=True, _scheme='https')
    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html", _external=True, _scheme='https')

@app.route("/logout")
@login_required
def logout():
    """Log user out."""
    id = session["user_id"]
    db.execute("UPDATE notification set status = 'read' WHERE user_id = :id",id=id)
    # forget any user_id
    session.clear()
    
    # redirect user to login form
    return redirect(url_for("login", _external=True, _scheme='https'))
 
    
@app.route('/fullmap')
@login_required
def fullmap():
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    
    if not lat:
        lat = 51.476852
        lon = -0.000500
    
    rows = db.execute("SELECT * FROM tracks")
    st = ""
    d = {}
    my_list = []
    for row in rows:
        d = {}
        icon = url_for('static',filename=row["catagory"]+".png")
        image = None
        if row["male_image"] != row["female_image"]:
            image = '<div class="col-md-6 col-sm-6 col-xs-6"><img style="height:100px;width:100px;border-radius:50%;" class="img-responsive" src="'+row["male_image"]+'"/><div class="h4 text-center">Male</div></div><div class="col-md-6 col-sm-6 col-xs-6"><img style="height:100px;width:100px;border-radius:50%;" class="img-responsive" src="'+row["female_image"]+'"/><div class="h5 text-center">Female</div></div>'
        else:
            image = '<div class="text-center col-md-12 col-sm-12 col-xs-12"><img style="height:100px;width:100px;border-radius:50%;" class="img-responsive" src="'+row["male_image"]+'"/><div class="h5 text-center">Male/Female</div></div>'
        cat = None
        if row["catagory"] == "eagleType":
            cat = 'Diurnal Raptor'
        elif row["catagory"] == "perchingBirds":
            cat = 'Perching Bird'
        elif row["catagory"] == "landBirds":
            cat = 'Landfowl'
        elif row["catagory"] == 'owl':  
            cat = 'Nocturnal Raptors'
        elif row["catagory"] == 'parakeet':
            cat = 'Parakeet'
        elif row["catagory"] == 'penguin':
            cat = 'Aquatic, Flightless'
        elif row["catagory"] == 'waterBird':
            cat = 'Waterfowl'
            
        d = {'icon':icon,'lat':row["lat"],'lng':row["long"],'infobox':'<div class="text-center h3">'+row["name"].title()+'</div>'+'<div class="text-center h5">Bird Type: '+cat+'</div>'+image+'<div class="text-center h5">Seen By: '+str(row["seen"])+' User(s)</div>'} 
        my_list.append(d)
    fullmap = Map(
        identifier="fullmap",
        varname="fullmap",
        style=(
            "height:100%;"
            "width:100%;"
            "top:0;"
            "left:0;"
            "position:absolute;"
            "z-index:200;"
        ),
        lat=lat,
        lng=lon,
 
        markers = my_list,
        maptype = "TERRAIN",
        zoom="17"
    )
    return render_template('track.html', fullmap=fullmap, _external=True, _scheme='https')

@app.route('/forgot',methods=["GET","POST"])
def forgot():
    if request.method == "POST":
        email = request.form.get("email")
        ans = request.form.get("ans")
        
        row = db.execute("SELECT * FROM users WHERE email = :email",email=email)
        if not row:
            flash("Email is not registered.")
            return render_template("forgot.html", _external=True, _scheme='https')
            
        if ans == row[0]["security_question"]:
            flash("Set new Password")
            return render_template("change.html",email=email, _external=True, _scheme='https')
        else:
            flash("Answer didn't matched with the original one.")
            return render_template("forgot.html", _external=True, _scheme='https')
    else:
        return render_template("forgot.html", _external=True, _scheme='https')

@app.route("/change",methods=["POST"])
def change():
    if request.method == "POST":
        if request.form["btn"] == "reset":
            password = request.form.get("password")
            confirm = request.form.get("confirm")
            email = request.form.get("email")
            
            if not password or not confirm:
                flash("Null value not allowed")
                return render_template("change.html",email=email, _external=True, _scheme='https')
            
            if not password == confirm:
                flash("Confirmation didnt matched")
                return render_template("change.html",email=email, _external=True, _scheme='https')
            
            encrypt = pwd_context.hash(request.form.get("password"))
            
            update = db.execute("UPDATE users SET password = :pword WHERE email = :email",pword=encrypt,email=email)
            if update:
                flash("Password updated successfully!")
                return render_template("index.html", _external=True, _scheme='https')
            else:
                flash("Error occured!")
                return render_template("index.html", _external=True, _scheme='https')
        else:
            return render_template("change.html", _external=True, _scheme='https')
    else:
        flash("Not Authorised")
        return redirect(url_for("logout", _external=True, _scheme='https'))
