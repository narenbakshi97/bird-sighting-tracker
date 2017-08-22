import math
from pygeocoder import Geocoder
import requests
from functools import wraps

import csv
import urllib.request

from flask import redirect, render_template, request, session, url_for
from functools import wraps


def getDistanceFromLatLonInKm(lat1,lon1,lat2,lon2):
  R = 6371
  dLat = deg2rad(lat2-lat1)
  dLon = deg2rad(lon2-lon1)
  a = math.sin(dLat/2) * math.sin(dLat/2) + math.cos(deg2rad(lat1)) * math.cos(deg2rad(lat2)) * math.sin(dLon/2) * math.sin(dLon/2)
  c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a)); 
  d = R * c
  return d

def deg2rad(deg):
  return deg * (3.14/180)
  
def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.11/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function