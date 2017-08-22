import os
import re
from flask import Flask,jsonify, flash, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import mkdtemp
from helper import *
from flask_googlemaps import GoogleMaps
from flask_googlemaps import Map,icons
from sqlalchemy import desc
from flask_sslify import SSLify

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://naren:root@localhost/finalproject'
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
db = SQLAlchemy(app)

# Tables
class Users(db.Model):
	id = db.Column(db.Integer,primary_key=True)
	name = db.Column(db.String(80))
	email = db.Column(db.String(120), unique=True)
	password = db.Column(db.String(120))
	security_question = db.Column(db.String(50))

	def __init__(self, name, email, password, security_question):
		self.name = name
		self.email = email
		self.password = password
		self.security_question = security_question

	def __repr__(self):
		return '<Users %r>' % self.name

class Tracks(db.Model):
	id = db.Column(db.Integer,primary_key=True)
	name = db.Column(db.String(80))
	lat = db.Column(db.Float(50))
	lon = db.Column(db.Float(50))
	seen = db.Column(db.Integer)
	catagory = db.Column(db.String(50))
	male_image = db.Column(db.String(200))
	female_image = db.Column(db.String(200))

	def __init__(self, name, lat, lon, seen, catagory, male_image, female_image):
		self.name = name
		self.lat = lat
		self.lon = lon
		self.seen = seen
		self.catagory = catagory
		self.male_image = male_image
		self.female_image = female_image

	def __repr__(self):
		return '<Tracks %r>' % self.name

class Notification(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer)
	message = db.Column(db.String(80))
	type = db.Column(db.String(50),default='perchingBirds')
	status = db.Column(db.String(10),default='unrerad')

	def __init__(self, user_id, message, type, status):
		self.user_id = user_id
		self.message = message
		self.type = type
		self.status = status

	def __repr__(self):
		return '<Notification %r>' % self.message

class Birds(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(80))
	male_image = db.Column(db.String(200))
	female_image = db.Column(db.String(200))

	def __init__(self, name, male_image, female_image):
		self.name = name
		self.male_image = male_image
		self.female_image = female_image

	def __repr__(self):
		return '<Birds %r>' % self.name

class Admin(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(50))
	type = db.Column(db.String(50),default='perchingBirds')
	male_image = db.Column(db.String(200))
	female_image = db.Column(db.String(200))
	lat = db.Column(db.Float(50))
	lon = db.Column(db.Float(50))
	user_id = db.Column(db.Integer)

	def __init__(self, name, type, male_image, female_image, lat, lon, user_id):
		self.name = name
		self.type = type
		self.male_image = male_image
		self.female_image = female_image
		self.lat = lat
		self.lon = lon
		self.user_id = user_id

	def __repr__(self):
		return '<Admin %r>' % self.name

@app.route('/')
def index():
	if session:
		notify = Notification.query.filter_by(user_id=session["user_id"], status='unread').all()
		history = Notification.query.filter_by(user_id=session["user_id"], status='read').order_by(desc(Notification.id)).all()
		if notify:
			count = Notification.query.filter_by(user_id = session["user_id"], status = 'unread').count()
			return render_template('index.html',notifications = notify,number=count,history=history, _external=True, _scheme='https')
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
			approve = Admin.query.all()
			return render_template('admin.html',rows=approve,results=results, _external=True, _scheme='https')

		elif request.form["btn"] == "Add To Database":
			name = request.form.get("name")
			m_image = request.form.get("m_image")
			f_image = request.form.get("f_image")
			q_id = request.form.get("q_id")
			uId = request.form.get("user")
			notify = Notification(uId,"Hey! We have added " + name + " into our database. Now you can track it. Thanks again for your contribution.")
			db.session.add(notify)
			db.session.commit()
			exe = Birds(name,m_image,f_image)
			db.session.add(exe)
			db.session.commit()
			if exe:
				delete = Admin.query.filter_by(id=q_id)
				db.session.delete(delete)
				db.session.commit()
				approve = Admin.query.all()
				return render_template('admin.html',rows=approve, _external=True, _scheme='https')

		elif request.form["btn"] == "Delete Request":
			q_id = request.form.get("q_id")
			delete = Admin.query.filter_by(id=q_id)
			db.session.delete(delete)
			db.session.commit()

			approve = Admin.query.all()
			return render_template('admin.html',rows=approve, _external=True, _scheme='https')

		elif request.form["btn"] == "Add TO Tracker":
			name = request.form.get("name")
			lat = float(request.form.get('lat'))
			lon = float(request.form.get('long'))
			m_image = request.form.get("male_image")
			f_image = request.form.get("female_image")
			catagory = request.form.get('catagory')
			uId = request.form.get("user")

			rows = Tracks.query.filter_by(name=name).all()
			notify = Notification(uId,"Hey! We have added " + name + " into the tracker. Thanks again for your contribution.",'track')
			db.session.add(notify)
			db.session.commit()
			if rows:
				for row in rows:
					if getDistanceFromLatLonInKm(lat,lon,row.lat,row.lon) < 5:
						track = Tracks.query.filter_by(id=row.id)
						track.seen = track.seen + 1
						db.session.commit()
						flash('Thankyou for your contribution')
						q_id = request.form.get("q_id")
						delete = Admin.query.filter_by(id=q_id)
						db.session.delete(delete)
						db.session.commit()
						approve = Admin.query.all()
				return render_template('admin.html',rows=approve,results=results, _external=True, _scheme='https')

			new_track = Tracks(name,lat,lon,1,catagory,m_image,f_image)
			db.session.add(new_track)
			db.session.commit()

			q_id = request.form.get("q_id")
			delete = Admin.query.filter_by(id=q_id)
			db.session.delete(delete)
			db.session.commit()

			approve = Admin.query.all()
			return render_template('admin.html',rows=approve,results=results, _external=True, _scheme='https')
		else:
			new_track = Tracks(name,lat,lon,1,catagory,m_image,f_image)
			db.session.add(new_track)
			db.session.commit()

			q_id = request.form.get("q_id")
			delete = Admin.query.filter_by(id=q_id)
			db.session.delete(delete)
			db.session.commit()

			approve = Admin.query.all()
			return render_template('admin.html',rows=approve,results=results, _external=True, _scheme='https')
	else:
		approve = Admin.query.all()
		return render_template('admin.html',rows=approve, _external=True, _scheme='https')

@app.route('/contribute',methods=['GET','POST'])
@login_required
def contribute():
	result = Birds.query.all()
	row = Users.query.filter_by(id=session["user_id"]).first()
	birds = request.form.get("bird")
	if birds:
		resends = Birds.query.filter(Birds.name.like("%"+birds+"%")).all()
		if resends:
			return render_template("contribute.html",resends=result,rows=result,username=session["user_id"], _external=True, _scheme='https')
		else:
			query = Admin(birds,'add',session["user_id"])
			db.session.add(query)
			db.session.commit()
			flash("Oops! We didn't find any similar result, We have registered your query, we will notify you")
			return redirect(url_for("contribute", _external=True, _scheme='https'))
	else:
		history = Notification.query.filter_by(user_id=session["user_id"],status="read").all()
		if history:
			return render_template("contribute.html",rows=result,username=session["user_id"],history=history, _external=True, _scheme='https')
		return render_template("contribute.html",rows=result,username=session["user_id"])

@app.route('/about')
@login_required
def about():
	history = Notification.query.filter_by(user_id=session["user_id"],status="read").all()
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
		known = Birds.query.filter_by(name=name).first()
		if known: 
			new_entry = Admin(name,"track",m_img,f_img,lat,lon,username)
			db.session.add(new_entry)
			db.session.commit()
			flash('Thankyou for your contribution')
			return redirect(url_for('index', _external=True, _scheme='https'))
	else:
		query = Admin.query.filter_by(name=name).first()
		query.lat = lat
		query.lon = lon 
		flash('Thankyou for your contribution')
		return redirect(url_for('index', _external=True, _scheme='https'))

@app.route('/register/',methods=["GET","POST"])
def register():
	if request.method == "POST":
		if request.form.get("password") != request.form.get("confirmation"):
			flash('Password and Confirmation didn\'t match')
			return render_template('register.html', _external=True, _scheme='https')
		crypt = pwd_context.hash(request.form.get("password"))
		check = Users.query.filter_by(email=request.form.get("email")).first()
		if check:
			flash("Sorry but this email address is already registered")
			return redirect(url_for("register", _external=True, _scheme='https'))
		user = Users(request.form.get("uname"),request.form.get("email"),crypt,request.form.get("question"))
		db.session.add(user)
		result = db.session.commit()
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
		rows = Users.query.filter_by(email=request.form.get("email")).first()

		encrypted = (request.form.get("password"))


		# ensure username exists and password is correct
		if not rows:
			flash("Email not registered")
			return redirect(url_for("login", _external=True, _scheme='https'))
		elif not pwd_context.verify(encrypted,rows.password):
			flash("Invalid password")
			return redirect(url_for('login', _external=True, _scheme='https'))

		# remember which user has logged in
		session["user_id"] = rows.id
		# redirect user to home page
		flash("Logged In successfully!")
		notify = Notification.query.filter_by(user_id=session["user_id"],status="unread").all()
		history = Notification.query.filter_by(user_id=session["user_id"],status="read").order_by(desc(Notification.id)).all()
		if notify:
			count = Notification.query.filter_by(user_id=session["user_id"],status="unread").count()
			return render_template('index.html',notifications = notify,number=count,history=history, _external=True, _scheme='https')
		return render_template('index.html',history=history, _external=True, _scheme='https')
		# else if user reached route via GET (as by clicking a link or via redirect)
	else:
		return render_template("login.html", _external=True, _scheme='https')

@app.route("/logout")
@login_required
def logout():
	"""Log user out."""
	id = session["user_id"]
	notify = Notification.query.filter_by(user_id=id)
	notify.status = 'read'
	db.session.commit()
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

	rows = Tracks.query.all()
	st = ""
	d = {}
	my_list = []
	for row in rows:
		d = {}
		icon = url_for('static',filename=row.catagory+".png")
		image = None
		if row.male_image != row.female_image:
			image = '<div class="col-md-6 col-sm-6 col-xs-6"><img style="height:100px;width:100px;border-radius:50%;" class="img-responsive" src="'+row.male_image+'"/><div class="h4 text-center">Male</div></div><div class="col-md-6 col-sm-6 col-xs-6"><img style="height:100px;width:100px;border-radius:50%;" class="img-responsive" src="'+row.female_image+'"/><div class="h5 text-center">Female</div></div>'
		else:
			image = '<div class="text-center col-md-12 col-sm-12 col-xs-12"><img style="height:100px;width:100px;border-radius:50%;" class="img-responsive" src="'+row.male_image+'"/><div class="h5 text-center">Male/Female</div></div>'
			cat = None

	if row.catagory == "eagleType":
		cat = 'Diurnal Raptor'
	elif row.catagory == "perchingBirds":
		cat = 'Perching Bird'
	elif row.catagory == "landBirds":
		cat = 'Landfowl'
	elif row.catagory == 'owl':  
		cat = 'Nocturnal Raptors'
	elif row.catagory == 'parakeet':
		cat = 'Parakeet'
	elif row.catagory == 'penguin':
		cat = 'Aquatic, Flightless'
	elif row.catagory == 'waterBird':
		cat = 'Waterfowl'

	d = {'icon':icon,'lat':row.lat,'lng':row.lon,'infobox':'<div class="text-center h3">'+row.name.title()+'</div>'+'<div class="text-center h5">Bird Type: '+cat+'</div>'+image+'<div class="text-center h5">Seen By: '+str(row.seen)+' User(s)</div>'} 
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

		row = Users.query.filter_by(email=email)
		if not row:
			flash("Email is not registered.")
			return render_template("forgot.html", _external=True, _scheme='https')

		if ans == row.security_question:
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

		user = Users.query.filter_by(email=email)
		user.password = encrypt
		db.session.commit()
		return render_template("change.html", _external=True, _scheme='https')
	else:
		flash("Not Authorised")
		return redirect(url_for("logout", _external=True, _scheme='https'))


if __name__ == "__main__":
	app.debug = True
	port = int(os.environ.get("PORT", 5000))
	app.run(host='0.0.0.0', port=port)