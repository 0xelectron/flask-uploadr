import soundcloud
from flask import Flask, request, redirect, url_for, render_template,abort
import os
import json
import glob
from uuid import uuid4

app = Flask(__name__)

p_dict = {}

client = soundcloud.Client(client_id='72ff54677f9e7c08c3764db576281f2a',
                           client_secret='34abea25446bd071992479ed18ad7847',
                           username='electron47',
                           password='DADA#blue9')

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload/<audio>", methods=["GET","POST"])
def upload(audio):

    if request.method == "POST":
        """Handle the upload of a file."""
        form = request.form

        tracks = []
        if audio == "tracks":
            tags = form.get("tag")
            t_p = form.get("playlist")
            n_p = client.get('/playlists/'+str(t_p))
            for track in n_p.tracks:
                tracks.append({'id':track['id']})
        else:
            tags = '\"\"Recent Satsang\"\"'

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

            if audio == "tracks":
                tracks.append({'id':track.id})

        # Add Tracks to playlist
        if audio == "tracks":
            client.put(n_p.uri, playlist={
                'tracks':tracks
            })

        if is_ajax:
            return ajax_response(True, upload_key)
        else:
            return redirect(url_for("upload_complete", uuid=upload_key))
    else:
        if audio == "tracks":
            playlists = client.get('/me/playlists')
            for playlist in playlists:
                p_dict[playlist.id] = playlist.title
            return render_template("track_upload.html", p_dict=p_dict,)

        elif audio == "recent_satsang":
            return render_template("satsang_upload.html")
        else:
            abort(404)



@app.route("/files/<uuid>")
def upload_complete(uuid):
    """The location we send them to at the end of the upload."""

    # Get their files.
    root = "uploadr/static/uploads/{}".format(uuid)
    if not os.path.isdir(root):
        return "Error: UUID not found!"

    files = []
    for file in glob.glob("{}/*.*".format(root)):
        fname = file.split("/")[-1]

        # # upload audio file
        # track = client.post('/tracks',track={
        #     'title': fname,
        #     'asset_data': open(file,'rb')
        #     })

        files.append(fname)

    return render_template("files.html",
        uuid=uuid,
        files=files,
    )


def ajax_response(status, msg):
    status_code = "ok" if status else "error"
    return json.dumps(dict(
        status=status_code,
        msg=msg,
    ))
