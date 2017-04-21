// playlist id
var pid = localStorage.getItem('recentsatsang') || null;

// TRACKS ARRAY
var TRACKS = [];

// download url
var suffix_url = "?oauth_token=" + localStorage.getItem('oauth_token');

// Info bar
var $infoBar = $("#info-bar");

// Parameters for Soundcloud Initialize
var PARAMS = {
        oauth_token: localStorage.getItem('oauth_token') || undefined,
        scope: 'non-expiring',
};

// Metalink Header
var M_HEADER = '<?xml version="1.0" encoding="UTF-8"?>' +
               '<metalink xmlns="urn:ietf:params:xml:ns:metalink">' +
               '<published>' + Date.now() + '</published>'

// Metalink Footer
var M_FOOTER = '</metalink>'


// Metalink Data
var M_DATA = M_HEADER

$(document).ready(function() {

    // Check for supported browser
    var isFirefox = typeof InstallTrigger !== 'undefined';
    if (!isFirefox) {
        $("#wrong-browser").append(
        '<div class="col-lg-4">' +
            '<div class="alert alert-dismissible alert-danger">' +
                '<button type="button" class="close" data-dismiss="alert">&times;</button> ' +
                '<strong>Oh snap!</strong> Currently, Soundcloud Downloader best works with ' +
                '<a href="https://www.mozilla.org/en-US/firefox/new/" class="alert-link">firefox ' +
                '</a> and <a href="https://addons.mozilla.org/en-gb/firefox/addon/downthemall/" ' +
                'class="alert-link">downthemall</a> extension for firefox.' +
            '</div>' +
        '</div>');
    }

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
    sq = sq.toLowerCase();

    // from date
    var fdate = document.forms["downloadTracksForm"]["from-date"].value || null;
    // to date
    var tdate = document.forms["downloadTracksForm"]["to-date"].value || null;
    if (!sq) {
        alert("You need to enter search querry");
        return;
    }
    if (!(fdate && tdate)) {
        alert("You need to enter from and to date");
        return;
    }
    fd = new Date(fdate);
    td = new Date(tdate);

    e.preventDefault();

    // is querry entered proper?
    if (re.test(sq)) {
        // get the list of tracks from playlist
        SC.get('/playlists/'+pid).then(function(playlist) {
            // for each track
            playlist.tracks.forEach(function(t) {
                // created at date for the track
                var cd = new Date(t.created_at);

                var title = t.title.toLowerCase();

                // is querry in track title and is track in range of
                // given date?
                if (title.search(sq) != -1 && cd >= fd && cd <= td)
                    TRACKS.push(t)
            });

            // generate metalink
            generateMetalink();

        })
    }
    else {
        reload(5, "Improper Query!", true);
        return;
    }
}

// generateMetalink: funtion to generate the
// metalink for tracks. To be downloaded from
// a supported downloader like downthemall in firefox
function generateMetalink() {

    // have we found any matching tracks?
    if (TRACKS.length < 1) {
        reload(10, "No matching tracks found!", true);
        return;
    }

    // for each track
    TRACKS.forEach(function(t) {

        // track title
        var title = t.title + '.mp3';
        // track url
        var url = t.download_url + suffix_url;
        // track size
        var size = t.original_content_size;

        // showInfo
        showInfo("Found " + tl + " Tracks! <br/> Now, Generating metalink...");

        // add track as file element in metalink
        addFileElement(title, size, url);

    });

    popUp();
    showInfo("Done! Hopefully a popup would have been generated in downthemall. " +
             "You can now select the tracks you want to download as well as " +
             "monitor its download progress.");
}

// addFileElement: function to add file metadata to metalink
// takes name, size and url as argument
function addFileElement(name, size, url) {
    var file = '<file name="' + name + '.mp3">' +
                '<size>' + size + '</size>' +
                '<url priority="1">' + url + '</url>' +
                '</file>'

    M_DATA += file
    return;
}

// popUp: function to popup metalink for download managers to grab
function popUp() {
        var a = document.createElement('a');
        document.body.appendChild(a);
        a.style = "display: none";
        M_DATA += M_FOOTER;
        var blob = new Blob([M_DATA], {type : 'application/metalink4+xml'});
        var url = URL.createObjectURL(blob);

        a.href = url;
        a.click();
        window.URL.revokeObjectURL(url);
        return;
}

// showInfo: function to show any info/error on
// the page
function showInfo(data, err=false) {
    // make infobar visible
    $infoBar.css('display', '');

    // is the info about any error?
    if (err)
        $infoBar.html('<p class="text-danger" align="center"> Error Occured: ' + data + '</p>');
    else
        $infoBar.html('<p class="text-success" align="center"> ' + data + '</p>');
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
