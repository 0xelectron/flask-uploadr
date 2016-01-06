# flask-uploadr
import soundcloud
from flask import Flask, request, redirect, url_for, render_template,abort
from flask_excel import make_response_from_array
import calendar
from dateutil import parser
import os
import shutil
import json
import glob
from uuid import uuid4

app = Flask(__name__)

# Initializing an soundcloud user
client = soundcloud.Client(client_id='YOUR CLIENT ID HERE',
                           client_secret='YOUR CLIENT SECRET HERE',
                           username='USERNAME',
                           password='PASSWORD')

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

        tags = form.get("tag")                          # Get tags
        t_p = form.get("playlist")                      # Get playlist id
        n_p = client.get('/playlists/'+str(t_p))        # Create url for playlist

        for track in n_p.tracks:
            tracks.append({'id':track['id']})           # Get previous tracks of playlist.

        # Create a unique "session ID" for this particular batch of uploads.
        upload_key = str(uuid4())

        # Is the upload using Ajax, or a direct POST by the form?
        is_ajax = False
        if form.get("__ajax", None) == "true":
            is_ajax = True

        # Target folder for these uploads.
        target = "uploadr/static/uploads/{}".format(upload_key)
        try:
            os.mkdir(target)
        except:
            if is_ajax:
                return ajax_response(False, "Couldn't create upload directory: {}".format(target))
            else:
                return "Couldn't create upload directory: {}".format(target)

        # Save files to disk.
        for upload in request.files.getlist("file"):
            filename = upload.filename.rsplit("/")[0]
            destination = "/".join([target, filename])
            upload.save(destination)

            # upload audio file to soundcloud
            track = client.post('/tracks',track={
                'title': filename,
                'asset_data': open(destination,'rb'),
                'tag_list':tags,
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
        playlists = client.get('/me/playlists')

        # Do we need to crearte tracks or satsang audio upload form ?
        if audio == "tracks":
            p_dict = {}
            for playlist in playlists:
                if not playlist.title == "Recent Satsang":
                    p_dict[playlist.id] = playlist.title
            return render_template("track_upload.html", p_dict=p_dict,)

        # We got GET to upload satsang audio. Prepare for it.
        elif audio == "recent_satsang":
            p_id = None
            p_title = None
            for playlist in playlists:
                if playlist.title == "Recent Satsang":
                    p_id=playlist.id
                    p_title=playlist.title
                    break

            # Did all go well?
            if p_id:
                return render_template("satsang_upload.html", p_id=p_id, p_title=p_title)
            else:
                # Didn't expect that.
                return "<h1>Didn't Find any Recent Satsang playlist. Make Sure to create one.</h1>"

        # He is lost Jarvis, let's tell him!
        else:
            abort(404)



# I'm Mitchel
@app.route("/files/<uuid>")
def upload_complete(uuid):
    """The location we send them to at the end of the upload."""

    # Get their files.
    root = "uploadr/static/uploads/{}".format(uuid)
    if not os.path.isdir(root):
        return "Error: UUID not found!"

    # Extract name from file address
    files = []
    for file in glob.glob("{}/*.*".format(root)):
        fname = file.split("/")[-1]
        files.append(fname)

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

        # Once Again! Get playlists
        t_p = form.get("playlist")
        n_p = client.get('/playlists/'+str(t_p))

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
        return make_response_from_array(xls_data, "csv")        # Send CSV

    # We got GET here, shaun!
    else:
        # Once Again! Get Playlist.
        p_dict = {}
        playlists = client.get('/me/playlists')

        # Prepare form
        for playlist in playlists:
            p_dict[playlist.id] = playlist.title

        # He's waiting for form, shaun!
        return render_template("export_data.html", p_dict=p_dict)

# I'm Mickey!
def ajax_response(status, msg):
    # How'd it go?
    status_code = "ok" if status else "error"

    # ajax wants json, Mickey!
    return json.dumps(dict(
        status=status_code,
        msg=msg,
    ))

