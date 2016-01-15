# flask-uploadr
import soundcloud
from flask import Flask, request, redirect, url_for, render_template,abort
from flask.ext import excel
import pyexcel.ext.xlsx
import calendar
from dateutil import parser
from collections import OrderedDict
import os
import sys
import shutil
import json
from uuid import uuid4

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Playlists per page
page_size = 70

# Initializing an soundcloud user
client = soundcloud.Client(client_id='YOUR CLIENT ID HERE',
                           client_secret='YOUR CLIENT SECRET HERE',
                           username='USERNAME',
                           password='PASSWORD')
def get_lists(url, ltype='playlists'):

    if ltype == 'playlists':
        playlists = []
        temp_playlists = client.get(url, limit=page_size,
                            linked_partitioning=1, representation='compact')
        while(True):
            for playlist in temp_playlists.collection:
                playlists.append(playlist)

            if hasattr(temp_playlists,'next_href'):
                temp_playlists = client.get(temp_playlists.next_href)
            else:
                break

        return playlists
    else:
        raise ValueError('The function yet doesn\'t know to extract lists other the playlists.')

# HomePage
@app.route("/")
def index():
    return render_template("index.html")

# I'm jarvis
@app.route("/upload/<audio>", methods=["GET","POST"])
def upload(audio):

    if request.method == "POST":                        # We Got POST!
        """Handle the upload of a file."""
        form = request.form                             # create form from request

        tracks = []

        tags = form.get("tag")                            # Get tags
        dbool = form.get("downloadable")                  # Get Checkbox
        pid = form.get("playlist")                        # Get playlist id
        n_p = client.get('/playlists/'+str(pid))          # Get playlist

        for track in n_p.tracks:
            tracks.append({'id':track['id']})           # Get previous tracks of playlist.

        # Create a unique "session ID" for this particular batch of uploads.
        upload_key = str(uuid4())

        # Is the upload using Ajax, or a direct POST by the form?
        is_ajax = False
        if form.get("__ajax", None) == "true":
            is_ajax = True

        # Target folder for these uploads.
        target = os.path.join(BASE_DIR,"static","uploads",upload_key)

        try:
            # try to create temporary directory
            os.mkdir(target)

        except Exception as e:

            # Show that something bad happened here! probably wasn't able to create directory
            sys.stderr.write("Error Occurred:" + str(e))

            if is_ajax:
                return ajax_response(False, "Couldn't create upload directory: {}".format(target))
            else:
                return "Couldn't create upload directory: {}".format(target)

        # Save files to disk.
        for upload in request.files.getlist("file"):
            destination = os.path.join(target, upload.filename)
            upload.save(destination)

            if not dbool:
                dbool = False

            # upload audio file to soundcloud
            track = client.post('/tracks',track={
                'title': upload.filename,
                'asset_data': open(destination,'rb'),
                'tag_list':tags,
                'downloadable':dbool,
                })

            # Append track to playlist
            tracks.append({'id':track.id})

        # Send tracks to playlist
        client.put(n_p.uri, playlist={
            'tracks':tracks
        })

        # All good jarvis!
        if is_ajax:
            return ajax_response(True, upload_key)
        else:
            return redirect(url_for("upload_complete", uuid=upload_key))
    else:

        # hmmm! Got an GET Request.
        # Get all playlists
        playlists = get_lists('/me/playlists')

        if audio == "tracks":
            p_dict = {}
            for playlist in playlists:
                p_dict[playlist.id] = playlist.title
            sp_dict = OrderedDict(sorted(p_dict.items(),key=lambda t: t[1]))
            return render_template("track_upload.html", p_dict=sp_dict,)

        # Create form to upload satsang audio.
        elif audio == "recent_satsang":
            rc_id = None
            rc_title = None
            for playlist in playlists:
                if playlist.title == "RecentSatsang":
                    rc_id=playlist.id
                    rc_title=playlist.title
                    break

            if rc_id:
                return render_template("satsang_upload.html", rc_id=rc_id, rc_title=rc_title)
            else:
                return "<h1>Didn't Find any Recent Satsang playlist. Make Sure to create one.</h1>"

        # He is lost Jarvis, let's tell him!
        else:
            abort(404)



# I'm Mitchel
@app.route("/files/<uuid>")
def upload_complete(uuid):
    """The location we send them to at the end of the upload."""

    # Get their files.
    root = os.path.join(BASE_DIR,"static","uploads",str(uuid))

    if not os.path.isdir(root):
        return "<h1>Error: UUID not found!</h1>"

    # Generate list of file currently uploaded
    files = [f for f in os.listdir(root)]

    # Clean up our Home
    shutil.rmtree(root)

    # All set to go, Mitchel!
    return render_template("files.html",
        uuid=uuid,
        files=files,
    )

# I'm shaun
@app.route("/export", methods=["GET","POST"])
def export_data():

    # We got POST, Shaun!
    if request.method == "POST":

        form = request.form
        # We will need friends
        timestamps = []
        t_data = {}
        xls_data = [['Track Name','Track ID','Play Count','Created At']]

        # Get Playlist Details
        pid = form.get("playlist")
        n_p = client.get('/playlists/'+str(pid))

        # Prepare data for sort
        for i, track in enumerate(n_p.tracks):
            timestamp = calendar.timegm(parser.parse(track['created_at']).timetuple())
            if not timestamp in timestamps:
                timestamps.append(timestamp)
                t_data[timestamp] = track
            else:
                timestamp += i;
                timestamps.append(timestamp)
                t_data[timestamp] = track

        # Sort Data in desecnding
        timestamps.sort(reverse=True)

        # join Data for CSV
        for timestamp in timestamps:
            track = t_data[timestamp]
            filename, extension = os.path.splitext(track['title'])
            xls_data.append([filename,track['id'],track['playback_count'],track['created_at']])

        # We Made it, shaun!
        return excel.make_response_from_array(xls_data, "xlsx")        # Send CSV

    # We got GET here, shaun!
    else:
        # Get all playlists
        playlists = get_lists('/me/playlists/')

        # Create form to upload  tracks.
        p_dict = {}
        for playlist in playlists:
            p_dict[playlist.id] = playlist.title

        # Sort the Playlist Dict.
        sp_dict = OrderedDict(sorted(p_dict.items(),key=lambda t: t[1]))

        # He's waiting for form, shaun!
        return render_template("export_data.html", p_dict=sp_dict)

# I'm Mickey!
def ajax_response(status, msg):
    # How'd it go?
    status_code = "ok" if status else "error"

    # ajax wants json, Mickey!
    return json.dumps(dict(
        status=status_code,
        msg=msg,
    ))

