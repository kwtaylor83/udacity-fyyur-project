# ----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
import datetime
from flask import (
    Flask,
    render_template,
    request,
    Response,
    flash,
    redirect,
    url_for
)
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import FlaskForm
from forms import ShowForm, VenueForm, ArtistForm
from flask_migrate import Migrate
import copy
from models import setup_db, Venue, Artist, Show

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = setup_db(app)

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
  recent_artists = Artist.query.filter(Artist.date_added is not None).order_by(Artist.date_added.desc()).limit(10).all()
  recent_venues = Venue.query.filter(Venue.date_added is not None).order_by(Venue.date_added.desc()).limit(10).all()
  return render_template('pages/home.html', recent_artists=recent_artists, recent_venues=recent_venues)

#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  """
    Returns the georgrphical areas for which we have Venues
  """
  areas = Venue.query.with_entities(Venue.city, Venue.state).group_by(Venue.state, Venue.city)

  data = []
  for area in areas:
    venues_in_this_area = []    
    venues = Venue.query.with_entities(Venue.id, Venue.name).filter_by(city=area.city, state=area.state)
    for venue in venues:
      upcoming_shows = Show.query.filter_by(venue_id=venue.id).count()
      venues_in_this_area.append({
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": upcoming_shows
      })

    data.append({
      "city": area.city,
      "state": area.state,
      "venues": venues_in_this_area
    })
  
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  """
    Returns Venues matching a given POST search string
  """
  venues = Venue.query.filter( 
    (Venue.name.ilike('%' + request.form.get('search_term') + '%')) | 
    (Venue.city.ilike('%' + request.form.get('search_term') + '%')) | 
    (Venue.state.ilike('%' + request.form.get('search_term') + '%')) 
    ).all()

  count = 0
  match_array = []
  for venue in venues:
    count += 1
    num_upcoming_shows = Show.query.filter_by(venue_id=venue.id).count()
    match_array.append({
      "id": venue.id,
      "name": venue.name,
      "num_upcoming_shows": num_upcoming_shows
    })
  response = {
    "count": count,
    "data": match_array
  }

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  """
  Returns a page showing the database details for the given venue,
  where the venue ID is supplied as a GET request parameter
  """
  venue = Venue.query.filter_by(id=venue_id).first()
  venue_shows = venue.venue_shows

  data = {
    'id': venue.id,
    'name': venue.name,
    'genres': venue.genres.replace("{","").replace("}","").split(","),
    'city': venue.city,
    'state': venue.state,
    'phone': venue.phone,
    'website_link': venue.website_link,
    'facebook_link': venue.facebook_link,
    'seeking_talent': venue.seeking_talent,
    'seeking_description': venue.seeking_description,
    'image_link': venue.image_link
  }
  
  past_shows_list = []
  upcoming_shows_list=[]  
  for show in venue_shows:
    show_artist = Artist.query.with_entities(Artist.name, Artist.image_link).filter_by(id=show.artist_id).first()
    this_show = {
      'artist_id': show.artist_id,
      'start_time': str(show.start_time)
    }
    this_show['artist_name'] = show_artist.name
    this_show['artist_image_link'] = show_artist.image_link
    if show.start_time < datetime.datetime.now():
      past_shows_list.append(this_show)
    else:
      upcoming_shows_list.append(this_show)

  data['past_shows'] =past_shows_list
  data['upcoming_shows'] = upcoming_shows_list
  data['past_shows_count'] = len(past_shows_list)
  data['upcoming_shows_count'] = len(upcoming_shows_list)

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  """
    Creates a database entry for a new Venue, the details of which are POSTed
  """
  form = VenueForm()
  if form.validate():
    name = form.name.data
    city = form.city.data
    state = form.state.data
    address = form.address.data
    phone = form.phone.data
    image_link = form.image_link.data
    genres = form.genres.data
    website_link = form.website_link.data
    facebook_link = form.facebook_link.data
    date_added = datetime.datetime.utcnow()

    try: 
      venue = Venue(name=name, city=city, state=state, address=address, phone=phone, image_link=image_link, genres=genres, website_link=website_link, facebook_link=facebook_link, date_added=date_added)
      db.session.add(venue)
      db.session.commit()
      flash('Venue ' + form.name.data + ' was successfully listed!')
      # TODO: insert form data as a new Venue record in the db, instead
      # TODO: modify data to be the data object returned from db insertion
    except Exception:
      db.session.rollback()
      flash('ERROR: Venue not added')
    finally:
      db.session.close()
  else:
    flash('ERROR: Venue not added, please check errors below:')
    return render_template('forms/new_venue.html', form=form)    
  
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return redirect(url_for('index'))

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  """
  Delete from the database the given, the ID is passed as a GET parameter
  """
  try:
    db.session.execute(
      "DELETE FROM \"Venue\" WHERE id=:param",
      {"param":venue_id}
    )
    db.session.commit()
  except Exception as e:
    flash("Error deleting venue: " + str(e))
  finally:
    db.session.close()

  return redirect(url_for('index'))


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  """
  GET request for all Artists in the database
  """
  artists = Artist.query.with_entities(Artist.id, Artist.name)

  return render_template('pages/artists.html', artists=artists)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  """
    Returns Artists matching a given POST search string
  """

  artists = Artist.query.filter(Artist.name.ilike('%' + request.form.get('search_term') + '%')).all()

  count = 0
  match_array = []
  for artist in artists:
    count += 1
    num_upcoming_shows = Show.query.filter_by(artist_id=artist.id).count()
    match_array.append({
      "id": artist.id,
      "name": artist.name,
      "num_upcoming_shows": num_upcoming_shows
    })
  response = {
    "count": count,
    "data": match_array
  }

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  """
  Returns a page showing the database details for the given artist,
  where the artist ID is supplied as a GET request parameter
  """

  artist = Artist.query.filter_by(id=artist_id).first()
  artist_shows = artist.artist_shows

  data = {
    'id': artist.id,
    'name': artist.name,
    'genres': artist.genres.replace("{","").replace("}","").split(","),
    'city': artist.city,
    'state': artist.state,
    'phone': artist.phone,
    'website_link': artist.website_link,
    'facebook_link': artist.facebook_link,
    'seeking_venue': artist.seeking_venue,
    'seeking_description': artist.seeking_description,
    'image_link': artist.image_link
  }
  
  past_shows_list = []
  upcoming_shows_list=[]  
  for show in artist_shows:
    show_venue = Venue.query.with_entities(Venue.name, Venue.image_link).filter_by(id=show.venue_id).first()
    this_show = {
      'venue_id': show.venue_id,
      'start_time': str(show.start_time)
    }
    this_show['venue_name'] = show_venue.name
    this_show['venue_image_link'] = show_venue.image_link
    if show.start_time < datetime.datetime.now():
      past_shows_list.append(this_show)
    else:
      upcoming_shows_list.append(this_show)

  data['past_shows'] =past_shows_list
  data['upcoming_shows'] = upcoming_shows_list
  data['past_shows_count'] = len(past_shows_list)
  data['upcoming_shows_count'] = len(upcoming_shows_list)

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  """
  Deliver a page showing the database details of the artist given as a GET parameter id.
  Allows users to edit and submit changes
  """
  artist = Artist.query.get(artist_id)
  form = ArtistForm(obj=artist)

  default_genres = artist.genres.replace("{","").replace("}","").split(",")
  form.genres.data = default_genres

  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  """
  Receives data from the edit artist page and stores changes in the database. 
  Artist ID is provided as a GET parameter and the form data is POSTed
  """

  form = ArtistForm()
  #if form.validate_on_submit():
  name = form.name.data
  city = form.city.data
  state = form.state.data
  phone = form.phone.data
  genres = form.genres.data
  website_link = form.website_link.data
  facebook_link = form.facebook_link.data
  image_link = form.image_link.data

  try: 
    artist = Artist.query.get(artist_id)
    artist.name = name
    artist.city = city
    artist.state = state
    artist.phone = phone
    artist.genres = genres
    artist.website_link = website_link
    artist.facebook_link = facebook_link
    artist.image_link = image_link
    
    db.session.commit()
    flash('Artist ' + form.name.data + ' was successfully updated!')
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
  except Exception as e: 
    db.session.rollback()
    flash('ERROR: Artist not updated')
  finally:
    db.session.close()  


  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  """
  Deliver a page showing the database details of the venue given as a GET parameter id.
  Allows users to edit and submit changes
  """  
  venue = Venue.query.get(venue_id)
  form = VenueForm(obj=venue)
  default_genres = venue.genres.replace("{","").replace("}","").split(",")
  form.genres.data = default_genres

  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  """
  Receives data from the edit venue page and stores changes in the database. 
  Venue ID is provided as a GET parameter and the form data is POSTed
  """
  form = VenueForm()
  # if form.validate_on_submit():
  name = form.name.data
  city = form.city.data
  state = form.state.data
  address = form.address.data
  phone = form.phone.data
  image_link = form.image_link.data
  genres = form.genres.data
  website_link = form.website_link.data
  facebook_link = form.facebook_link.data

  try: 
    venue = Venue.query.get(venue_id)
    venue.name = name
    venue.city = city
    venue.state = state
    venue.address = address
    venue.phone = phone
    venue.image_link = image_link
    venue.facebook_link = facebook_link
    venue.website_link = website_link
    venue.genres = genres

    db.session.commit()
    flash('Venue ' + form.name.data + ' was successfully updated!')
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
  except Exception:
    db.session.rollback()
    flash('ERROR: Venue not updated')
  finally:
    db.session.close()

  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  """
  Create a new artist in the database, the artist details are POSTed
  """
  form = ArtistForm()
  if form.validate():
    name = form.name.data
    city = form.city.data
    state = form.state.data
    phone = form.phone.data
    image_link = form.image_link.data
    genres = form.genres.data
    website_link = form.website_link.data
    facebook_link = form.facebook_link.data
    date_added = datetime.datetime.utcnow()  
    available_hours = form.available_hours.data

    try: 
      artist = Artist(name=name, city=city, state=state, phone=phone, image_link=image_link, genres=genres, website_link=website_link, facebook_link=facebook_link, date_added=date_added, available_hours=available_hours)
      db.session.add(artist)
      db.session.commit()
      flash('Artist ' + form.name.data + ' was successfully listed!')
      # TODO: insert form data as a new Venue record in the db, instead
      # TODO: modify data to be the data object returned from db insertion
    except Exception as e: 
      db.session.rollback()
      flash('ERROR: Artist not added, there was an error writing to the database: ' + str(e))
      return render_template('forms/new_artist.html', form=form)
    finally:
      db.session.close()  
  else: 
    flash('ERROR: Artist not added, please check errors below:')
    return render_template('forms/new_artist.html', form=form)

  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion

  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  return redirect(url_for('index'))


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  """
  Returns shows.html and lists all shows in the database
  """
  upcoming_shows = Show.query.filter(Show.start_time >= datetime.datetime.now()).all()

  data = []
  for show in upcoming_shows:
    this_show = {}
    this_show["venue_id"] = show.venue_id
    this_show["venue_name"] = show.venue.name
    this_show["artist_id"] = show.artist_id
    this_show["artist_name"] = show.artist.name
    this_show["artist_image_link"] = show.artist.image_link
    this_show["start_time"] = str(show.start_time)
    data.append(this_show)

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  """
  Received POSTed form data for a new show and saves those details in the database
  Returns user to index.html
  """
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  
  form = ShowForm()
  if form.validate():
    artist_id = form.artist_id.data
    venue_id = form.venue_id.data
    start_time = form.start_time.data

    # Isolate hour from desired show time
    start_time_only = str(start_time).split(' ')[1]
    start_time_hour = int(start_time_only[0] + start_time_only[1])

    # Get start and end hours for artist availability
    artist = Artist.query.get(artist_id)
    available_from = 0
    available_to = 23
    available_hours = artist.available_hours
    if available_hours:
      available_from = int(available_hours.split('-')[0])
      available_to = int(available_hours.split('-')[1])

    # If show time falls in Artist available hours, or no available hours were specified for the artist, try to list the show
    if (start_time_hour >= available_from) and (start_time_hour <= available_to):
      try: 
        show = Show(artist_id=artist_id, venue_id=venue_id, start_time=start_time)
        db.session.add(show)
        db.session.commit()
        flash('Show was successfully listed!')
        # TODO: insert form data as a new Venue record in the db, instead
        # TODO: modify data to be the data object returned from db insertion
      except Exception as e:
        db.session.rollback()
        flash('ERROR: Show not created!')
      finally:
        db.session.close()  
    else:
      flash("Artist not avaiable at that time")

  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return redirect(url_for('index'))

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
