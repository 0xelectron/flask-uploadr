# flask-uploadr

This is app is forked from <a href="https://github.com/kirsle/flask-multi-upload">flask-multi-upload</a>. Thanks to <a href="https://github.com/kirsle">kirle</a>.

This app just presents an 2 HTML form full of the usual types of input elements (text boxes), and a multi-file input box, and an HTML5 drag/drop target for dragging files from your PC into the page.

It demonstrates that you can combine a multi-file upload form along with other form data (i.e. letting a user choose playlists and tags to upload the tracks into). There's also a live progress bar that tells you the current progress of the upload. It doesn't break it down by individual file though, to keep things simpler.

It's backwards compatible and also works with clients that have scripts disabled. The same endpoint is used on the back-end to handle the form post and file upload; when the Ajax calls the endpoint, the Flask app uploads the tracks the souncloud using python api returns a JSON response including the "unique ID" chosen for the upload, and then the JavaScript on the front-end initiates a redirect. With scripts disabled (so that the form will POST directly to the back-end), a normal HTTP redirect is given to the final results page.

It works in most modern browsers and Internet Explorer 10+.
