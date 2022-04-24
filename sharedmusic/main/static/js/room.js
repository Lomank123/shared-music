const roomCode = $("#room").attr("room_code");
const urlField = document.getElementById("url-field");
const audio_tag = document.getElementById("youtube");
const connectionString =
    "ws://" + window.location.host + "/ws/room/" + roomCode + "/";
const roomSocket = new WebSocket(connectionString);
const username = $("#user").attr("username");
let hostUsername = $("#host").attr("host_username");
let player;
const audioPlayer = document.querySelector(".audio-player");
// Need to give host username
let users = [];
isFirstClick = true;

// connect function is called only when player is ready
function connect() {
    roomSocket.onopen = () => {
        console.log("WebSocket connection created.");
        roomSocket.send(
            JSON.stringify({
                event: "CONNECT",
                message: username,
            })
        );
    };

    roomSocket.onclose = (e) => {
        console.log("Closing connection...");
    };

    roomSocket.onmessage = (e) => {
        let data = JSON.parse(e.data);
        data = data["payload"];
        console.log(data);

        if (data.event == "CONNECT") {
            document.getElementById("users-count").innerHTML =
                data.listeners.count.toString();
            updatePlaylist(data.playlist);
        }
        if (data.event == "SEND_TRACK_TO_NEW_USER") {
            console.log(player.getPlayerState());
            let state = player.getPlayerState();
            const trackData = {
                name: player.getVideoData().title,
                duration: player.getDuration(),
                url: player.getVideoUrl(),
                currentTime: player.getCurrentTime(),
                isPaused: state == 2 || state == -1,
            };
            roomSocket.send(
                JSON.stringify({
                    event: "NEW_USER_JOINED",
                    message: "New user joined.",
                    user: data.receiver,
                    track: trackData,
                })
            );
        }
        if (data.event == "DISCONNECT") {
            document.getElementById("users-count").innerHTML =
                data.listeners.count.toString();
        }
        if (data.event == "ALREADY_CONNECTED") {
            roomSocket.close();
            console.log("Closing connection. Refresh the page.");
        }
        if (data.event == "CHANGE_TRACK") {
            const id = youtube_parser(data.track.url);
            player.loadVideoById(id);
            playTrack();
            updatePlaylist(data.playlist, data.track.url);
        }
        if (data.event == "ADD_TRACK") {
            // display new track in playlist with buttons
            updatePlaylist(data.playlist);
        }
        if (data.event == "SET_CURRENT_TRACK") {
            const id = youtube_parser(data.track.url);
            player.loadVideoById(id, data.track.currentTime);
            playTrack();
            if (data.track.isPaused) {
                //player.mute();
                setTimeout(() => {
                    pauseTrack();
                    //player.unMute();
                }, 500)
            }
            updatePlaylist(data.playlist, data.track.url);
        }
        if (data.event == "PLAY") {
            playTrack();
        }
        if (data.event == "PAUSE") {
            pauseTrack();
        }
        if (data.event == "CHANGE_TIME") {
            player.seekTo(data.time);
        }
    };

    if (roomSocket.readyState == WebSocket.OPEN) {
        roomSocket.onopen();
    }
}

function clearPlaylist() {
    let playlist = document.getElementById("playlist");
    playlist.innerHTML = '';
}

function updatePlaylist(newPlaylist, url='') {
    clearPlaylist();
    let playlist = document.getElementById("playlist");
    newPlaylist.forEach(track => {
        let trackBlock = document.createElement("p");
        trackBlock.textContent = track.name;
        if (url === track.url) {
            trackBlock.style.fontWeight = 'bold';
        }
        playlist.appendChild(trackBlock);
        trackBlock.addEventListener('click', (e) => {changeTrack(e, track)});
    });
}

function changeTrack(event, trackData) {
    roomSocket.send(
        JSON.stringify({
            event: "CHANGE_TRACK",
            message: "Change track.",
            track: trackData,
        })
    );
}

function onYouTubeIframeAPIReady() {
    player = new YT.Player("player", {
        height: "360",
        width: "640",
        videoId: "",
        events: {
            onReady: onPlayerReady,
            onStateChange: onPlayerStateChange,
        },
    });
}

function onPlayerReady(event) {
    //document.getElementById(ui.play).addEventListener("click", togglePlay);
    //timeupdater = setInterval(initProgressBar, 100);
    audioPlayer.querySelector(".time .length").textContent = getTimeCodeFromNum(
        player.getDuration()
    );
    mutePlayer();
    //player.setVolume(75);
    audioPlayer.querySelector(".name").textContent =
        player.getVideoData().title;

    // Set click listener to the whole page
    document.addEventListener('mouseup', firstClickListener);
    function firstClickListener(event) {
        if (isFirstClick) {
            isFirstClick = false;
            unMutePlayer();
            console.log("No longer muted!");
            document.getElementById('mute-msg').style.display = 'none';
        }
    }

    connect();
}

function onPlayerStateChange(event) {
    if (event.data == YT.PlayerState.ENDED) {
        //document.getElementById(ui.play).classList.add("pause");
        //document.getElementById(ui.percentage).style.width = 0;
        //document.getElementById(ui.currentTime).innerHTML = "00:00";
        //player.seekTo(0, true);
    }
    audioPlayer.querySelector(".time .length").textContent = getTimeCodeFromNum(
        player.getDuration()
    );
    audioPlayer.querySelector(".name").textContent =
        player.getVideoData().title;
}

//click on timeline to skip around
const timeline = audioPlayer.querySelector(".timeline");
timeline.addEventListener(
    "click",
    (e) => {
        const timelineWidth = window.getComputedStyle(timeline).width;
        const timeToSeek =
            (e.offsetX / parseInt(timelineWidth)) * player.getDuration();
        player.seekTo(timeToSeek);
        roomSocket.send(
            JSON.stringify({
                event: "CHANGE_TIME",
                time: timeToSeek,
                message: "Change time.",
            })
        );
    },
    false
);

//click volume slider to change volume
const volumeSlider = audioPlayer.querySelector(".controls .volume-slider");
volumeSlider.addEventListener(
    "click",
    (e) => {
        const sliderWidth = window.getComputedStyle(volumeSlider).width;
        const newVolume = e.offsetX / parseInt(sliderWidth);
        player.setVolume(newVolume * 100);
        audioPlayer.querySelector(".controls .volume-percentage").style.width =
            newVolume * 100 + "%";
    },
    false
);

//check audio percentage and update time accordingly
setInterval(() => {
    const progressBar = audioPlayer.querySelector(".progress");
    progressBar.style.width =
        (player.getCurrentTime() / player.getDuration()) * 100 + "%";
    audioPlayer.querySelector(".time .current").textContent =
        getTimeCodeFromNum(player.getCurrentTime());
}, 500);

//toggle between playing and pausing on button click
const playBtn = audioPlayer.querySelector(".controls .toggle-play");
playBtn.addEventListener(
    "click",
    () => {
        if (player.getPlayerState() === 1) {
            pauseTrack();
            roomSocket.send(
                JSON.stringify({
                    event: "PAUSE",
                    message: "Track is now paused.",
                })
            );
        } else {
            playTrack();
            roomSocket.send(
                JSON.stringify({
                    event: "PLAY",
                    message: "Track is now playing",
                })
            );
        }
    },
    false
);

const volumeEl = audioPlayer.querySelector(".volume-container .volume");

audioPlayer.querySelector(".volume-button").addEventListener("click", () => {
    if (!player.isMuted()) {
        mutePlayer();
    } else {
        unMutePlayer();
    }
});

function mutePlayer() {
    player.mute();
    volumeEl.classList.remove("icono-volumeMedium");
    volumeEl.classList.add("icono-volumeMute");
}

function unMutePlayer() {
    player.unMute();
    volumeEl.classList.add("icono-volumeMedium");
    volumeEl.classList.remove("icono-volumeMute");
}

//turn 128 seconds into 2:08
function getTimeCodeFromNum(num) {
    let seconds = parseInt(num);
    let minutes = parseInt(seconds / 60);
    seconds -= minutes * 60;
    const hours = parseInt(minutes / 60);
    minutes -= hours * 60;

    if (hours === 0) return `${minutes}:${String(seconds % 60).padStart(2, 0)}`;
    return `${String(hours).padStart(2, 0)}:${minutes}:${String(
        seconds % 60
    ).padStart(2, 0)}`;
}

function youtube_parser(url) {
    var code = url.match(/v=([^&#]{5,})/);
    return typeof code[1] == "string" ? code[1] : false;
}

function addTrack() {
    const id = youtube_parser(urlField.value);
    if (id) {
        roomSocket.send(
            JSON.stringify({
                event: "ADD_TRACK",
                url: urlField.value,
                message: "Add new track.",
            })
        );
    } else {
        roomSocket.send(
            JSON.stringify({
                event: "ADD_TRACK_ERROR",
                message: "Could not find audio url.",
            })
        );
    }
}

function pauseTrack() {
    playBtn.classList.remove("pause");
    playBtn.classList.add("play");
    player.pauseVideo();
}

function playTrack() {
    playBtn.classList.remove("play");
    playBtn.classList.add("pause");
    player.playVideo();
}
