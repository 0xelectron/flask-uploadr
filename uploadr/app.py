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
try:
    client = soundcloud.Client(client_id='YOUR_CLIENT_ID',
                               client_secret='YOUR_CLIENT_SECERET',
                               username='USERNAME',
                               password='PASSWORD')
except Exception as e:
    sys.stderr.write("Error Occured: {}".format(e))

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

def export_data(pid):

    tids = []
    t_data = {}
    xls_data = [['Track Name','Track ID','Playback count','Duration']]

    # Get Playlist Details
    n_p = client.get('/playlists/'+str(pid))

    # Prepare data for sort
    for track in n_p.tracks:
        tids.append(track['id'])
        t_data[track['id']] = track

    # Sort Data in desecnding
    sorted(tids, key=lambda s: str(s).lower())

    # join Data for CSV
    for tid in tids:
        track = t_data[tid]
        try:
            trackid = str(track['id']) + "|" +  str(track['secret_token'])
        except KeyError:
            trackid = str(track['id']) + "|"
        except Exception as e:
            sys.stderr.write("Error Ocurred while preparing for excel sheet: %s".format(e))
            trackid = str(track['id']) + "|"

        filename, extension = os.path.splitext(track['title'])
        xls_data.append([filename,trackid,track['playback_count'],track['duration']])

    return excel.make_response_from_array(xls_data, "xlsx")        # Send CSV

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

        pid = form.get("playlist")                        # Get playlist id

        if request.form['submit'] == "Export":
            if not pid == "None":
                return export_data(pid)
            else:
                return html_response("Select the Playlist!")
        else:

            tracks = []

            tags = form.get("tag")                            # Get tags
            dbool = form.get("downloadable")                  # Get Downloadable status
            sharing = form.get("public")                      # Get Sharing status
            n_playlist = form.get("n_playlist")               # Try to Get new playlist

            # Is the upload using Ajax, or a direct POST by the form?
            is_ajax = False
            if form.get("__ajax", None) == "true":
                is_ajax = True

            """ We only need one of the two fields, not Both. Check about that!"""
            cond1 = (n_playlist and (pid and pid != "None"))
            cond2 = (not n_playlist) and (pid == "None" or not pid)

            if (cond1 or cond2):
                if is_ajax:
                    return ajax_response(False, "You need to either select playlist or enter new playlist title. Not Both or None")
                else:
                    return html_response("You need to either select playlist or enter new playlist title. Not Both or None")

            if request.files.getlist("file")[0].filename == "":
                if is_ajax:
                    return ajax_response(False, "You might want to add files")
                else:
                    return html_response("You might want to add files")

            # Create a unique "session ID" for this particular batch of uploads.
            upload_key = str(uuid4())

            # Target folder for these uploads.
            target = os.path.join(BASE_DIR,"static","uploads",upload_key)

            try:
                # try to create temporary directory
                os.mkdir(target)

            except Exception as e:
                # Show that something bad happened here! probably wasn't able to create directory
                sys.stderr.write("Error Occured: {}".format(e))

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
                if not sharing:
                    sharing = "private"

                try:
                    # upload audio file to soundcloud
                    track = client.post('/tracks',track={
                        'title': os.path.splitext(upload.filename)[0],
                        'asset_data': open(destination,'rb'),
                        'tag_list':tags,
                        'downloadable':dbool,
                        'sharing':sharing,
                        })

                    # Append track to playlist
                    tracks.append({'id':track.id})

                except Exception as e:
                    sys.stderr.write("Error Occured: {}".format(e))

            """ Get Previous tracks of the playlist and update the playlist."""
            if (pid != "None" and (not n_playlist)):
                try:
                    n_p = client.get('/playlists/'+str(pid))        # Get playlist
                    for track in n_p.tracks:
                        tracks.append({'id':track['id']})           # Get previous tracks of playlist.

                    client.put(n_p.uri, playlist={                  # Update Playlist
                        'tracks':tracks
                    })

                except Exception as e:
                    sys.stderr.write("Error Occured: {}".format(e))

            else:
                try:
                    client.post("/playlists",playlist={
                        'title': n_playlist,
                        'sharing':'private',
                        'tracks':tracks,
                    })

                except Exception as e:
                    sys.stderr.write("Error Occured: {}".format(e))

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
            sp_dict = OrderedDict(sorted(p_dict.items(),key=lambda t: t[1].lower()))
            return render_template("track_upload.html", p_dict=sp_dict,)

        # Create form to upload satsang audio.
        elif audio == "recent_satsang":
            rc_id = None
            rc_title = None
            for playlist in playlists:
                if (playlist.title).lower().replace(" ","") == "recentsatsang":
                    rc_id=playlist.id
                    rc_title=playlist.title
                    break

            if rc_id:
                return render_template("satsang_upload.html", rc_id=rc_id, rc_title=rc_title)
            else:
                return html_response("""Didn't Find any Recent Satsang playlist. Make Sure to create one or
                        Check for any typo!""")

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

# # I'm shaun
# @app.route("/export", methods=["GET","POST"])
# def export_data():

#     # We got POST, Shaun!
#     if request.method == "POST":

#         form = request.form
#         tids = []
#         t_data = {}

#         xls_data = [['Track Name','Track ID','Playback count','Duration']]

#         # Get Playlist Details
#         pid = form.get("playlist")
#         n_p = client.get('/playlists/'+str(pid))

#         # Prepare data for sort
#         for track in n_p.tracks:
#             tids.append(track['id'])
#             t_data[track['id']] = track

#         sorted(tids, key=lambda s: s.lower())

#         # join Data for CSV
#         for tid in tids:
#             track = t_data[tid]
#             try:
#                 trackid = str(track['id']) + "|" +  str(track['secret_token'])
#             except KeyError:
#                 trackid = str(track['id']) + "|"
#             except Exception as e:
#                 sys.stderr.write("Error Ocurred while preparing for excel sheet: %s".format(e))
#                 trackid = str(track['id']) + "|"

#             filename, extension = os.path.splitext(track['title'])
#             xls_data.append([filename,trackid,track['playback_count'],track['duration']])


#         # We Made it, shaun!
#         return excel.make_response_from_array(xls_data, "xlsx")        # Send CSV

#     # We got GET here, shaun!
#     else:
#         # Get all playlists
#         playlists = get_lists('/me/playlists/')

#         # Create form to upload  tracks.
#         p_dict = {}
#         for playlist in playlists:
#             p_dict[playlist.id] = playlist.title

#         # Sort the Playlist Dict.
#         sp_dict = OrderedDict(sorted(p_dict.items(),key=lambda t: t[1].lower()))

#         # He's waiting for form, shaun!
#         return render_template("export_data.html", p_dict=sp_dict)

# I'm Mickey!
def ajax_response(status, msg):
    # How'd it go?
    status_code = "ok" if status else "error"

    # ajax wants json, Mickey!
    return json.dumps(dict(
        status=status_code,
        msg=msg,
    ))

def html_response(msg):
    response = """
    <strong>Oh snap!</strong><p>{}</p><a href="/"><h3>Home</h3></a>
    """.format(msg)
    return response

# if __name__ == "__main__":
#     app.run()
