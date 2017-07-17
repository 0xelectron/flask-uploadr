#################################################################
# soundcloud-uploadr                                            #
# Copyright (c) 2016 0xelectron                                 #
#################################################################


from flask import Flask, request, render_template, abort, session
import soundcloud
import logging
import logging.handlers

LOG_FILENAME = "uploadr_log.out"

my_logger = logging.getLogger('UploadrLogger')
my_logger.setLevel(logging.DEBUG)

# Add the log message handler to the logger
handler = logging.handlers.RotatingFileHandler(
              LOG_FILENAME, maxBytes=10*1024*1024, backupCount=5)

my_logger.addHandler(handler)

app = Flask(__name__)

# Connect to soundcloud
def connectToSoundcloud():
    try:
        client = soundcloud.Client( client_id='CLIENT_ID',
                                    client_secret='CLIENT_SECRET',
                                    username='USERNAME',
                                    password='PASSWORD' )

        session['oauth_token'] = client.access_token
        session.permanent = True

    except Exception as e:
        sys.stderr.write("Error Occured while connecting to soundcloud: {}".format(e))

# Check Connection
def checkConnection():
    try:
        client = soundcloud.Client(access_token=session['oauth_token'])
        client.get('/me')
    except Exception as e:
        session.clear()
        connectToSoundcloud()

# HomePage
@app.route("/")
def index():
    checkConnection()
    return render_template("index.html")

# @app.route("/callback")
# def callback():
#     return render_template("callback.html")

@app.route("/upload/<audio>")
def upload(audio):
    checkConnection()

    if audio == "recent-satsang":
        return render_template("satsang_upload.html", oauth_token=session['oauth_token'])
    elif audio == "kids-stories":
        return render_template("kids_stories_upload.html", oauth_token=session['oauth_token'])
    elif audio == "tracks":
        return render_template("track_upload.html", oauth_token=session['oauth_token'])
    else:
        abort(404)

@app.route("/download")
def download_tracks():
    checkConnection()
    return render_template("download_tracks.html", oauth_token=session['oauth_token'])

if __name__ == "__main__":
    # flask_options = dict(
    #     host='localhost',
    #     port=2006,
    #     threaded=True,
    # )
    app.secret_key = 'C(@WDiuTP796%yZH*zcfOssgvdifhYmZ'
    # app.run(**flask_options)

    from gevent.wsgi import WSGIServer
    address = "localhost", 2006
    server = WSGIServer(address, app,
        log=my_logger, error_log=my_logger)
    try:
        print("Server running on port %s:%d. Ctrl+C to quit" % address)
        server.serve_forever()
    except KeyboardInterrupt:
        server.stop()
        print("Bye bye")
