/******************************************************************************
 * soundcloud-uploadr                                                         *
 * Copyright (c) 2016 0xelectron                                              *
 ******************************************************************************/

// Max size
var MAX_UPLOAD_FILE_SIZE = 1024*1024*500; // 500 MB

// Current url
var URL = window.location.href;

// Number of results per request.
var PAGE_SIZE = 70;

// Parameters for Soundcloud Initialize
var PARAMS = {
        // client_id: 'YOUR_CLIENT_ID',
        // redirect_uri: 'YOUR_CALLBACK_URL_AS_IN_YOUR_APP',
        oauth_token: localStorage.getItem('oauth_token') || undefined,
        scope: 'non-expiring',
};

// Make Playlists selection searchable
var $select = $('#playlist').selectize({
    maxItems: 1,
    valueField: 'id',
    labelField: 'title',
    searchField: 'title',
    create: false,
    closeAfterSelect: true,
    selectonTab: true,
});
var SELECT = $select[0].selectize;

//You can upload AIFF, WAVE (WAV), FLAC, ALAC, OGG, MP2, MP3, AAC, AMR, and WMA files.
//Following files types will be added: audio/x-ms-wma,audio/mp3,audio/x-m4a,audio/flac
var FILE_TYPES = ['audio/x-ms-wma','audio/mp3','audio/mpeg','audio/ogg','audio/x-m4a','audio/flac','audio/x-wav'];

// List of pending files to handle when the Upload button is finally clicked.
var PENDING_FILES  = [];

// Dropbox
var DROP = document.getElementById("dropbox");

// Progress Bar
var $progressBar = $("#progress-bar");

// Calculate total Progress.
var PROGRESS = {};

// Check if need to upload recent satsang.
var RECENT = URL.search("recent-satsang");

var USERNAME = localStorage.getItem("username") || null;

$(document).ready(function() {

    if ( USERNAME ){
        $("#username").append('<a href="https://www.soundcloud.com/' + USERNAME + '" > Hi ' + USERNAME + '!</a>');
    }
    // Set up SoundCloud
    setupSoundcloud();

    // Initialize Form
    initForm();

    // Set up the drag/drop zone.
    initDropbox();

    // Set up the handler for the file input box.
    $("#file-picker").on("change", function() {
        handleFiles(this.files);
    });

    // Handle the upload button.
    $("#upload-button").on("click", function(e) {
        // Check if we are connected to soundcloud?
        if ( SC.isConnected() ){
            // Validate Form
            validateForm(e);
        } else {
            alert("you need to connect to soundcloud");
            $("#connect").show();
            return;
        }
    })
    // Handle the export button.
    $("#export-button").on("click",function(e){
        // Check if we are connected to soundcloud?
        if ( SC.isConnected() ){
            // check if it's recent-satsang page?
            if ( RECENT > 0 ){
                e.preventDefault();
                // create csv data file.
                exportData(e, localStorage.getItem("recentsatsang"));
            } else {
                // Check if we have playlist selected?
                var x = document.forms["uploadForm"]["playlist"].value || null;
                if ( x === "None" || !x ){
                    alert("You need to Select Playlist.");
                    e.preventDefault()
                    return;
                }
                // create csv data file.
                exportData(e, x);
            }
        } else {
            alert("you need to connect to soundcloud");
            $("#connect").show();
            return;
        }
    });
});

// // function to check soundcloud connection.
// function checkConnection(){
//     // Make sure we really are.
//     SC.get("me").then( ( me ) => {
//         console.info( "Logged in!" );
//         $("#connect").hide();
//     }, ( err ) => {
//         console.error('Problem logging in: %o', err);
//         // Is oauth token expired?
//         if (err.status === 401) {
//             window.location.reload(true);
//             connectToSoundcloud();
//         } else {
//             throw err;
//         }
//     }).catch( (err) => {
//         alert("Error: " + err.message + " ! Check console for more info.");
//         console.log("Error occured during Connecting to soundcloud. Try refreshing!");
//         console.log(err);
//     });
// };

// function to connect to soundcloud.
function connectToSoundcloud() {

    // Connect and save oauth token to local storage.
    SC.connect().then( ( { oauth_token } ) => {

        localStorage.setItem('oauth_token', oauth_token);
        console.info('Connected! (probably)');
        return SC.get('/me');

        }).then( (userdata) => {
            // We're In.
            localStorage.setItem('username', userdata.username);
            console.info('Logged in!');
            $("#connect").hide();
        }, ( err ) => {
            console.error('Problem logging in: %o', err);
            // Is oauth token expired?
            if (err.status === 401) {
                window.location.reload(true);
            } else {
                throw err;
            }
    // Error connecting to soundcloud.
    }).catch((err) => {
        alert("Error: " + err.message + " ! Check console for more info.");
        console.log("Error occured during Connecting to soundcloud. Try refreshing!");
        console.log(err);
    });
};

// function to set up Soundcloud api
function setupSoundcloud(){

    // Initialize.
    SC.initialize( PARAMS );

    // Connect.
    if ( SC.isConnected() ) {
        $("#connect").hide();
        // checkConnection();
    }
    else {
        connectToSoundcloud();
    }

};

// function to get all the Playlists recursively.
// takes playlists object as argument.
function getPlaylists ( playlists ){

    // Loop through all playlists.
    for ( var i in playlists.collection ) {
        var pl = playlists.collection[i];
        // Add playlist to select option.
        SELECT.addOption(pl);
        // Refresh select option.
        SELECT.refreshOptions();
        // Also add recentsatsang playlist id to localstorage.
        if ( !localStorage.getItem('recentsatsang') ) {
            if ( pl.title.toLowerCase().replace(/ /g,'') === "recentsatsang" ) {
                localStorage.setItem('recentsatsang', pl.id);
            }
        }
    }
    // Do we still have more playlists?
    if ( playlists.hasOwnProperty( "next_href" ) ){
        // fetch them.
        SC.get(playlists.next_href.slice(26)).then(getPlaylists);
    }
    return;
}

// function to initialize form.
function initForm() {

    // set total progress to 0.
    PROGRESS = {};

    // hide progress bar
    $("#progress").hide();

    // is is recent-satsang page?
    if ( RECENT > 0 && localStorage.getItem('recentsatsang') ){
        return;
    }
    // Call getPlaylists to get all playlists recursively.
    SC.get('/me/playlists', {
      limit: PAGE_SIZE, linked_partitioning: 1,
      representation: "compact",
    }).then(getPlaylists);

    // Set up tag field.
    $('#tags').selectize({
        delimiter: ',',
        persist: false,
        create: function(input) {
            return {
                value: input,
                text: input
            }
        }
    });
}

// function to create new playlist.
// takes playlist title and tracks as argument.
function createPlaylist ( title, tracks ){

    // create playlist.
    // default sharig = private.
    SC.post('/playlists', {
        playlist: {
            title: title,
            tracks: tracks,
            sharing: "private",
        }
        // catch any errors.
    }).then( (e) =>{
        DROP.innerHTML = '<p class="text-danger" align="center"> Done';
        // Reload after 3 seconds.
        setTimeout(function() {
            window.location.reload(true)}, 3000);
    }).catch(function(err){
        alert("Error: " + err.message + " ! Check console for more info.");
        console.log("Error occured during creating playlist");
        console.log(err);

    });

}

// function to update Playlist.
// takes playlist id and tracks as argument.
function updatePlaylist ( pid, tracks ){

    if (!pid){
        alert("Error: Couldn't update playlist. Check console for more info.");
        console.log("Error: didn't get playlist id. Try Refresing!");
    }
    // Get previous Tracks
    SC.get('/playlists/' + pid).then(function(playlist) {
      playlist.tracks.forEach(function(track) {
          tracks.push({'id':track.id});
      });
      // Update Playlist
     return SC.put('/playlists/' + pid, {
         playlist: { tracks: tracks }
     });
     // Catch any errors.
    }).then( ( e ) => {
        DROP.innerHTML = '<p class="text-danger" align="center"> Done';
        // Reload after 3 seconds
        setTimeout(function() {
            window.location.reload(true)}, 3000);
    }).catch(function(err){
        alert("Error: " + err.message + " ! Check console for more info.");
        console.log("Error occured during updating playlist");
        console.log(err);
    });

}

// function to upload tracks.
// takes form data as argument.
function uploadTracks ( fd ){

    // get all files to be uploaded.
    var files = fd.getAll("file");
    // get total number of files.
    var len = files.length;
    // filename.
    var name;
    // playlist id.
    var pid;
    // list of tracks( new and previous ).
    var tracks = [];
    // list of promises.
    var promises = [];
    // for every file
    for ( var i = 0; i < len; i++ ) {
        name = files[i].name.split(".",2)[0];
        // start uploading and add promise to promises.
        // downloadable = false(default)
        // sharing = private(default)
        promises.push(SC.upload({
            file: files[i],
            title: name,
            tag_list: fd.get("tags"),
            downloadable: fd.get("downloadable") || false,
            sharing: fd.get("public") || "private",
            progress: progress,
        }));
    }
    // resolve all promises before moving further.
    Promise.all(promises).then(function(tr){
        for ( var i in tr ){
            // add tracks to list of tracks.
            tracks.push({'id':tr[i].id});
        }

        // create new playlist?

        if ( fd.has("n_playlist") && fd.get("n_playlist") != "" ) {
            createPlaylist(fd.get("n_playlist"), tracks );
        } else {
            // is it recent-satsang page?
            if ( RECENT > 0 ) {
                // grab playlist id from localstorage.
                pid = localStorage.getItem("recentsatsang");
            } else {
                // grab playlist id from select option.
                pid = fd.get("playlist");
            }
            // update playlist.
            updatePlaylist(pid, tracks);
        }

    });
}

// function to calculate total progress.
// takes progress event as argument.
function progress( e ){
    var p = 0;
    // update current file progress.
    PROGRESS[e.total] = (e.loaded / e.total) * 100;
    // add total progress of all files.
    for ( var obj in PROGRESS ) {
        p += PROGRESS[obj];
    }
    // calculate total mean progress.
    p /= PENDING_FILES.length;
    // update progress bar.
    $progressBar.css({"width" : p + "%"});
    p = Math.round(p);
    DROP.innerHTML = '<p class="text-danger" align="center"> Uploading(' + p + '%)';
    if ( p >= 100 ){
        DROP.innerHTML = '<p class="text-danger" align="center"> Uploaded. Updating Playlist...';
    }
    return;
}

// function to create csv data file.
// takes event and playlist id as argument.
function exportData(e, pid ){

    e.preventDefault();
    csvRows = []
    var tids = [];
    var tData = {};

    // insert header.
    rowData = [['Track Name', 'Track ID', 'Playback Count', 'Duration']]

    // Get track Data
    SC.get('/playlists/' + pid).then(function(playlist) {
        playlist.tracks.forEach(function(track) {
            tids.push(track.id);
            tData[track.id] = track;
        });

        // Sort Data in desecnding
        tids.sort(function(a, b){
            return a > b ? 1 : a < b ? -1 : 0;
        }).reverse();

        // join Data for CSV
        for ( var i in tids ){
            var track = tData[tids[i]];
            // track id contains track id and secret token.
            var trackid = track['id'] + "|";
            if ( track.hasOwnProperty('secret_token') ) {
                trackid += track['secret_token'];
            }
            // insert new row
            rowData.push([track['title'], trackid, track['playback_count'], track['duration']])
        }

        // join rows
        for (var i = 0, l = rowData.length; i < l; ++i) {
            csvRows.push(rowData[i].join(','));
        }

        var csvString = csvRows.join("\n");
        var a = document.createElement('a');
        a.href = 'data:attachment/csv,' + encodeURIComponent(csvString);
        a.target = '_blank';
        if (rowData.length > 1) {
            a.download = String(pid) + '.csv';
        } else {
            a.download = 'empty.csv';
        }
        document.body.appendChild(a);
        a.click();

    });
    return;
}

// function to validate form
// takes event as argument
function validateForm(e) {

    var upload = true;
    e.preventDefault();

    // is it recent-satsang page?
    if ( RECENT > 0 ){
        // Are files selected?
        if ( PENDING_FILES.length == 0 && upload == true ){
            alert("You may want to add files!");
            upload = false;
            return;
        } else {
            // Start uploading.
            doUpload();
        }
    } else {

        var x = document.forms["uploadForm"]["playlist"].value || null;
        var y = document.forms["uploadForm"]["n_playlist"].value || null;
        if ( x === "None" ){
            x = null;
        }
        if ( y === ""){
            y = null;
        }

        if ( x && y ){
            alert("You need to either select playlist or enter new playlist title to create playlist. Not Both");
            upload = false;
            return;
        }

        else if ( !x && !y ){
            alert("You need to either select playlist or enter new playlist title to create playlist. Not None");
            upload = false;
            return;
        }

        else if ( PENDING_FILES.length == 0 && upload == true ){
            alert("You may want to add files!");
            upload = false;
            return;
        }
        else {
            // start uploading.
            doUpload();
        }
    }
}

// function to handle uploads.
function doUpload() {

    // show progress bar
    $("#progress").show();

    // Gray out the form.
    $("#uploadForm :input").attr("disabled", "disabled");

    // Initialize the progress bar.
    $progressBar.css({"width": "0%"});

    // Collect the form data.
    fd = collectFormData();

    // Attach the files.
    for (var i = 0, ie = PENDING_FILES.length; i < ie; i++) {
        fd.append("file", PENDING_FILES[i]);
    }
    // start uploading tracks.
    uploadTracks( fd );

    return;

}

// function to collect form data.
function collectFormData() {
    // Go through all the form fields and collect their names/values.
    var fd = new FormData();

    $("#uploadForm :input").each(function() {
        var $this = $(this);
        var name  = $this.attr("name");
        var type  = $this.attr("type") || "";
        var value = $this.val();

        // No name = no care.
        if (name === undefined) {
            return;
        }

        // Skip the file upload box for now.
        if (type === "file") {
            return;
        }

        // Checkboxes? Only add their value if they're checked.
        if (type === "checkbox" || type === "radio") {
            if (!$this.is(":checked")) {
                return;
            }
        }

        fd.append(name, value);
    });

    return fd;
}

// function to handle files selected.
// takes files as argument.
function handleFiles(files) {
    // Add them to the pending files list.
    var p_f_t = true;
    for (var i = 0, ie = files.length; i < ie; i++) {

        if($.inArray(files[i].type, FILE_TYPES) >= 0){
            PENDING_FILES.push(files[i]);
        }else{
            p_f_t = false;
        }
    }
    if (p_f_t == false){
        alert("some files have not been added as only audio file types are supported");
    }
    DROP.innerHTML = '<p class="text-success" align="center">' + PENDING_FILES.length + ' files ready for upload';
}

// function to handle drag and drop of files.
function initDropbox() {
    var $dropbox = $("#dropbox");
    var drop = DROP;

    // On drag enter...
    $dropbox.on("dragenter", function(e) {
        e.stopPropagation();
        e.preventDefault();
        $(this).addClass("active");
    });

    // On drag over...
    $dropbox.on("dragover", function(e) {
        e.stopPropagation();
        e.preventDefault();
    });

    // On drop...
    $dropbox.on("drop", function(e) {
        e.preventDefault();
        $(this).removeClass("active");

        // Get the files.
        var files = e.originalEvent.dataTransfer.files;
        handleFiles(files);

        // Update the display to acknowledge the number of pending files.
        // $dropbox.text(PENDING_FILES.length + "files ready for upload!");
        // drop.innerHTML = '<p class="text-success" align="center">' + PENDING_FILES.length + ' files ready for upload';
    });

    // If the files are dropped outside of the drop zone, the browser will
    // redirect to show the files in the window. To avoid that we can prevent
    // the 'drop' event on the document.
    function stopDefault(e) {
        e.stopPropagation();
        e.preventDefault();
    }
    $(document).on("dragenter", stopDefault);
    $(document).on("dragover", stopDefault);
    $(document).on("drop", stopDefault);
}
