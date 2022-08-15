#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
from operator import itemgetter
from unicodedata import name
import dateutil.parser
import babel
from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'venues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    genres = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship('Show', backref='venue', lazy=True) 

class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    website_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship('Show', backref='artist', lazy=True)

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
class Show(db.Model):
    __tablename__ = 'shows'
    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def show_artist(self):
        return {
            'artist_id': self.artist_id,
            'artist_name': self.artist.name,
            'artist_image_link': self.artist.image_link,
            'start_time': self.start_time.strftime('%Y-%m-%d %H:%M:%S')
        }

    def show_venue(self):
        return {
            'venue_id': self.venue_id,
            'venue_name': self.venue.name,
            'venue_image_link': self.venue.image_link,
            'start_time': self.start_time.strftime('%Y-%m-%d %H:%M:%S')
        }

  
# db.create_all()

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  venues = Venue.query.filter().order_by(Venue.city, Venue.name, Venue.state)
  data = []
  
  city = None
  state = None
  data_venues = {}
  for venue in venues:
    if (city != venue.city) and (state != venue.state):
      if city is not None:
        data.append(data_venues)
      city = venue.city
      data_venues = {}
      data_venues["city"] = venue.city
      data_venues["state"] = venue.state
      data_venues["venues"] = []
    d = {}
    d["id"] = venue.id
    d["name"] = venue.name
    d["num_upcoming_shows"] = len(venue.shows)     
    data_venues['venues'].append(d)

  data.append(data_venues)
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on venues with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"  
  search_term = request.form["search_term"]
  venues = Venue.query.filter(Venue.name.ilike("%"+search_term+"%"))
  data = []
  for venue in venues:
    data.append({
      "id": venue.id,
      "name": venue.name,
      "num_upcoming_shows": len(venue.shows)
    })

  response = {}
  response["count"] = len(data)
  response["data"] = data
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  venue = Venue.query.get(venue_id)
  past_shows = list(filter(lambda x: x.start_time < datetime.today(), venue.shows))
  upcoming_shows = list(filter(lambda x: x.start_time >= datetime.today(), venue.shows))
  past_shows = list(map(lambda x: x.show_artist(), past_shows))
  upcoming_shows = list(map(lambda x: x.show_artist(), upcoming_shows))
  data = {
    "id": venue_id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website_link,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows": upcoming_shows,
    "upcoming_shows_count": len(upcoming_shows)
  }
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  
  # TODO: modify data to be the data object returned from db insertion
  error = False
  form = VenueForm(request.form)
  if request.method == "POST" and form.validate():
    print(form.name.data)
    try:
      venue = Venue(
        name = form.name.data,
        city = form.city.data,
        state = form.state.data,
        address = form.address.data,
        phone = form.phone.data,
        image_link = form.image_link.data,
        genres = form.genres.data,
        facebook_link = form.facebook_link.data,
        website_link = form.website_link.data,
        seeking_talent = form.seeking_talent.data,
        seeking_description = form.seeking_description.data
      )
      db.session.add(venue)
      db.session.commit()
    except Exception:
      error = True
      db.session.rollback()
    finally:
      db.session.close()
    if not error:
      # on successful db insert, flash success
      flash('Venue ' + request.form['name'] + ' was successfully listed!')
    else:
      flash('An error occurred. Show could not be listed.')
  else:
    flash(form.errors)

  # on successful db insert, flash success
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  venue = Venue.query.get(venue_id)
  eror = False
  body = {}
  if venue:
    name = venue.name
    try:
      db.session.delete(venue)
      db.session.commit()
      body['delete'] = True
      body['url'] = url_for('index')
    except:
      eror = True
      db.session.rollback()
    finally:
      db.session.close()
    if not eror:
      flash('Venue ' + name + ' was successfully deleted!')
      return jsonify(body)
    flash('An error occurred deleting venue '+name+'.')
  else:
    flash('An error occurred. Venue could not be deleted.')
    return redirect(url_for('venues'))

  # return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  artists = Artist.query.order_by(Artist.name).all()
  data = []
  for a in artists:
      data.append({
          "id": a.id,
          "name": a.name
      })
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_term = request.form.get('search_term')
  search_results = Artist.query.filter(Artist.name.ilike('%{}%'.format(search_term))).all()

  response = {}
  response['count'] = len(search_results)
  response['data'] = search_results
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  artist = Artist.query.get(artist_id)
  print(artist)
  past_shows = list(filter(lambda x: x.start_time < datetime.today(), artist.shows)) 
  upcoming_shows = list(filter(lambda x: x.start_time >= datetime.today(), artist.shows))
  past_shows = list(map(lambda x: x.show_venue(), past_shows))
  upcoming_shows = list(map(lambda x: x.show_venue(), upcoming_shows))

  data = {
      "id": artist_id,
      "name": artist.name,
      "genres": artist.genres,
      "city": artist.city,
      "state": artist.state,
      "phone": artist.phone,
      "website": artist.website_link,
      "facebook_link": artist.facebook_link,
      "seeking_venue": artist.seeking_venue,
      "seeking_description": artist.seeking_description,
      "image_link": artist.image_link,
      "past_shows": past_shows,
      "past_shows_count": len(past_shows),
      "upcoming_shows": upcoming_shows,
      "upcoming_shows_count": len(upcoming_shows)
  }
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.get(artist_id)
  if not artist:
      return redirect(url_for('index'))
  form = ArtistForm(obj=artist)
  artist = {"id": artist_id, "name": artist.name, "genres": artist.genres, "city": artist.city, "state": artist.state, "phone": artist.phone, "website": artist.website_link, "facebook_link": artist.facebook_link, "seeking_venue": artist.seeking_venue, "seeking_description": artist.seeking_description, "image_link": artist.image_link}
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  error = False
  form = ArtistForm(request.form)
  if request.method == "POST" and form.validate():
    try:
      edit_artist = Artist.query.get(artist_id)
      edit_artist.name = form.name.data
      edit_artist.city = form.city.data
      edit_artist.state = form.state.data
      edit_artist.phone = form.phone.data
      edit_artist.genres = form.genres.data
      edit_artist.seeking_venue = form.seeking_venue.data
      edit_artist.seeking_description = form.seeking_description.data
      edit_artist.image_link = form.image_link.data
      edit_artist.website_link = form.website_link.data
      edit_artist.facebook_link = form.facebook_link.data
      db.session.commit()
    except Exception:
      error = True
      db.session.rollback()
    finally:
      db.session.close()
    if not error:
      # on successful db insert, flash success
      flash('Artist ' + request.form['name'] + ' was successfully edited!')
    else:
      flash('An error occurred. Artist ' + form.name.data + ' could not be edited.')
  else:
    flash(form.errors)

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    venue = Venue.query.get(venue_id)
    if not venue:
        return redirect(url_for('index'))
    form = VenueForm(obj=venue)
    venue = {"id": venue_id, "name": venue.name, "genres": venue.genres, "address": venue.address, "city": venue.city, "state": venue.state, "phone": venue.phone, "website": venue.website_link, "facebook_link": venue.facebook_link, "seeking_talent": venue.seeking_talent, "seeking_description": venue.seeking_description, "image_link": venue.image_link}
    return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  error = False
  form = VenueForm(request.form)
  if request.method == "POST" and form.validate():
    try:
      edit_venue = Venue.query.get(venue_id)
      edit_venue.name = form.name.data
      edit_venue.city = form.city.data
      edit_venue.state = form.state.data
      edit_venue.address = form.address.data
      edit_venue.phone = form.phone.data
      edit_venue.genres = form.genres.data
      edit_venue.seeking_talent = form.seeking_talent.data
      edit_venue.seeking_description = form.seeking_description.data
      edit_venue.image_link = form.image_link.data
      edit_venue.website_link = form.website_link.data
      edit_venue.facebook_link = form.facebook_link.data
      db.session.commit()
    except Exception:
      error = True
      db.session.rollback()
    finally:
      db.session.close()
    if not error:
      # on successful db insert, flash success
      flash('Venue ' + request.form['name'] + ' was successfully edited!')
    else:
      flash('An error occurred. Venue ' + form.name.data + ' could not be edited.')
  else:
    flash(form.errors)
  
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  error = False
  form = ArtistForm(request.form)
  if request.method == "POST" and form.validate():
    try:
      artists = Artist(
        name = form.name.data,
        city = form.city.data,
        state = form.state.data,
        phone = form.phone.data,
        image_link = form.image_link.data,
        genres = form.genres.data,
        facebook_link = form.facebook_link.data,
        website_link = form.website_link.data,
        seeking_venue = form.seeking_venue.data,
        seeking_description = form.seeking_description.data
      )
      db.session.add(artists)
      db.session.commit()
    except Exception:
      error = True
      db.session.rollback()
    finally:
      db.session.close()
    if not error:
      # on successful db insert, flash success
      flash('Artist ' + request.form['name'] + ' was successfully listed!')
    else:
      flash('An error occurred. Artist ' + form.name.data + ' could not be listed.')
  else:
    flash(form.errors)
  # TODO: modify data to be the data object returned from db insertion

  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  shows = Show.query.all()
  data = []
  for s in shows:
      data.append({
          "venue_id": s.venue.id,
          "venue_name": s.venue.name,
          "artist_id": s.artist.id,
          "artist_name": s.artist.name,
          "artist_image_link": s.artist.image_link,
          "start_time": format_datetime(str(s.start_time))
      })
  
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  form = ShowForm(request.form)
  error = False
  if request.method == "POST" and form.validate():
    try:
      shows = Show(
        artist_id = form.artist_id.data,
        venue_id = form.venue_id.data,
        start_time = form.start_time.data
      )
      db.session.add(shows)
      db.session.commit()
    except Exception:
      error = True
      db.session.rollback()
    finally:
      db.session.close()
    if not error:
      # on successful db insert, flash success
      flash('Show was successfully listed!')
      # return redirect(url_for("index"))
      return render_template('pages/home.html')
    else:
      flash('An error occurred. Show could not be listed.')
      # abort(400)
  else:
    flash(form.errors)
    return render_template('forms/new_show.html', form=form)

  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
