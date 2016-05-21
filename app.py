#############################################################
# soundcloud-uploadr                                        #
# Copyright (c) 2016 0xelectron                             #
#############################################################


from flask import Flask, request, render_template,abort

app = Flask(__name__)

# HomePage
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/callback")
def callback():
    return render_template("callback.html")

@app.route("/upload/<audio>")
def upload(audio):

    if audio == "recent-satsang":
        return render_template("satsang_upload.html")
    elif audio == "tracks":
        return render_template("track_upload.html")
    else:
        abort(404)

if __name__ == "__main__":
    flask_options = dict(
        host='localhost',
        port=2006,
        threaded=True,
    )
    app.run(**flask_options)
