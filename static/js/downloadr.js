// playlist id
var pid = localStorage.getItem('recentsatsang') || null;

// TRACKS ARRAY
var TRACKS = [];

// download url
var suffix_url = "?oauth_token=" + localStorage.getItem('oauth_token');

// Number of results per request.
var PAGE_SIZE = 1;

// Progress Bar
var $progressBar = $("#progress-bar");

// Info bar
var $infoBar = $("#info-bar");

// Parameters for Soundcloud Initialize
var PARAMS = {
        oauth_token: localStorage.getItem('oauth_token') || undefined,
        scope: 'non-expiring',
};


// to collect tracks in zip
var ZIP = new JSZip();

$(document).ready(function() {

    // Initialize.
    SC.initialize( PARAMS );

    // Do we have playlist id?
    if (pid == null) {
        alert("Please click on Add Recent Satsang tab" +
        " so I can grab playlist id. (Only for first time)");
        return;
    }

    // Handle the download button
    $("#download-button").on("click", function(e) {

        // Check if we are connected to soundcloud?
        if ( SC.isConnected() ){
            downloadTracks(e);
        } else {
            alert("You're not Connected. Try refreshing.");
            return;
        }
    });
});


// function to download the tracks matching 
// the given query
function downloadTracks(e) {

    // only alphanumeric querry allowed
    var re = new RegExp("[a-zA-Z0-9!@#$&()\\-`.+,/\" ]*$")

    // entered querry
    var sq = document.forms["downloadTracksForm"]["search-query"].value || null;

    e.preventDefault();

    // show prgress and info bars
    $("#progress").css('display', '');
    $infoBar.css('display', '');

    // is querry entered proper?
    if (sq != null && re.test(sq)) {
        // get the list of tracks from playlist
        SC.get('/playlists/'+pid).then(function(playlist) {
            // for each track 
            playlist.tracks.forEach(function(t) {
                // is querry in track title?
                if (t.title.search(sq) != -1)
                    TRACKS.push(t)
            });

            // generate zip
            generateZip();

        })
    }
    else {
        reload(5, "Improper Query!", true);
        return;
    }
}

// funtion to download the tracks from given url
// and gnereate a zip of downloaded tracks
function generateZip() {

    // show Progress
    progress(0);

    // to count the end of loop
    var count = 0;
    var tl = TRACKS.length;
    var p = 0.0;

    // have we found any matching tracks?
    if (tl < 1) {
        reload(10, "No matching tracks found!", true);
        return;
    }

    // for each track
    TRACKS.forEach(function(t) {

        // track title
        var title = t.title;
        // track url
        var url = t.download_url + suffix_url;

        // showInfo
        showInfo("Found " + tl + " Tracks! <br/> Now, Downloading...");

        // get track from url
        JSZipUtils.getBinaryContent(url, function(err, data) {

            // any error?
            if(err) {
                reload(10, err, true);
                return;
            }

            // add track to our zip container
            ZIP.file(title+'.mp3', data, {binary: true});

            count++;
            p = Math.round((count * 100.0) / tl);
            progress(p);
            showInfo(p + "%");

            // have we downloaded all tracks?
            if (count == tl){
                // hide prgress bar
                $("#progress").css('display', 'none');

                // generate zip 
                ZIP.generateAsync({type:"blob"})
                    .then(function (blob) {
                        saveAs(blob, "tracks.zip");
                        setTimeout(function() {
                            reload(5, "Done!")}, 3000);
                    }, function(err) {
                        reload(m=err, err=true);
                    });
            }

        });
    });
}

// showInfo: function to show any info/error on
// the page
function showInfo(data, err=false) {
    // is the info about any error?
    if (err)
        $infoBar.html('<p class="text-danger" align="center"> Error Occured: ' + data + '</p>');
    else
        $infoBar.html('<p class="text-success" align="center"> ' + data + '</p>');
}

// progress: function to calculate total progress.
// takes progress event as argument.
function progress(p){

    // update progress bar.
    $progressBar.css({"width" : p + "%"});

    return;
}

// reload: function to reload after t seconds
// showing msg m
function reload(t=3, m=none, err=false) {

    m += "<br/> Note: Reloading window in " + t + " secs."

    // show msg
    if (err) 
        showInfo(m, true)
    else
        showInfo(m)

    // Reload after t seconds.
    setTimeout(function() {
        window.location.reload(true)}, t * 1000);
}
