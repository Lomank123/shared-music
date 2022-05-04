const roomCode = $("#room").attr("room_code");
const urlField = document.getElementById("url-field");
const audio_tag = document.getElementById("youtube");
const protocol = window.location.protocol == "https:" ? "wss://" : "ws://";
let roomSocket = null;
const connectionString = protocol + window.location.host + "/ws/room/" + roomCode + "/";
const username = $("#user").attr("username");
let hostUsername = $("#host").attr("host_username");
let player;
const audioPlayer = document.querySelector(".audio-player");
const usersList = document.getElementById("users-list");
// Need to give host username
let users = [];
// Indicates whether user has clicked on window
isFirstClick = true;
const ytApiKey = "AIzaSyCp-e6T1qe6QqgjH6JydzBHCjB2raF6FrE";

// Player elements
const timeline = document.querySelector(".timeline");
const progressBar = document.querySelector(".progress");
const volumeEl = document.querySelector(".volume-container .volume");
const volumeSlider = document.querySelector(".controls .volume-slider");
const playBtn = document.querySelector(".controls .toggle-play");
const thumb = document.querySelector(".name .thumb");
// connect function is called only when player is ready
function connect() {
    roomSocket = new WebSocket(connectionString);
    roomSocket.onopen = () => {
        showContent();
        console.log("WebSocket connection created.");
        roomSocket.send(
            JSON.stringify({
                event: "CONNECT",
                message: username,
            })
        );
    };

    roomSocket.onerror = (e) => {
        console.log("WebSocket error.");
    };

    roomSocket.onclose = (e) => {
        let text = "Closing connection...";
        if (e.code === 1006) {
            text += " Attempting to reconnect...";
            setTimeout(function () {
                connect();
            }, 10000);
        }

        pauseTrack();
        // reconnect in 10 secs (player will be reloaded correctly)
    };

    roomSocket.onmessage = (e) => {
        let data = JSON.parse(e.data);
        data = data["payload"];
        console.log(data);

        if (data.event == "CONNECT") {
            //document.getElementById("users-count").innerHTML = data.listeners.count.toString();
            users = data.listeners.users;
            while (usersList.hasChildNodes()) {
                usersList.removeChild(usersList.firstChild);
            }
            users.forEach((user) => {
                let node = $(
                    `<li>` +
                        `<div class="online"></div>` +
                        `<div class="username">${user.username}</div>` +
                        `</li>`
                );
                $("#users-list").append(node);
            });
            if (username === data.user) {
                updatePlaylist(data.playlist);
            }
        }
        if (data.event == "SEND_TRACK_TO_NEW_USER") {
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
            //document.getElementById("users-count").innerHTML = data.listeners.count.toString();
            users = data.listeners.users;
            while (usersList.hasChildNodes()) {
                usersList.removeChild(usersList.firstChild);
            }
            users.forEach((user) => {
                let node = $(
                    `<li>` +
                        `<div class="online"></div>` +
                        `<div class="username">${user.username}</div>` +
                        `</li>`
                );
                $("#users-list").append(node);
            });
        }
        if (data.event == "ALREADY_CONNECTED") {
            roomSocket.close(1000, (reason = "qweqweqweS"));
            console.log("Closing connection. Refresh the page.");
        }
        if (data.event == "CHANGE_TRACK") {
            const id = youtube_parser(data.track.url);
            setThumbnail(id);
            player.loadVideoById(id);
            playTrack();
            updatePlaylist(data.playlist, data.track.url);
        }
        if (data.event == "ADD_TRACK") {
            // display new track in playlist with buttons
            updatePlaylist(data.playlist, player.getVideoUrl());
        }
        if (data.event == "SET_CURRENT_TRACK") {
            const id = youtube_parser(data.track.url);
            setThumbnail(id);
            player.loadVideoById(id, data.track.currentTime);
            playTrack();
            if (data.track.isPaused) {
                //player.mute();
                setTimeout(() => {
                    pauseTrack();
                    //player.unMute();
                }, 500);
            }
            updatePlaylist(data.playlist, data.track.url);
        }
        if (data.event == "DELETE_TRACK") {
            updatePlaylist(data.playlist, data.chosenTrackUrl);
            if (player.getVideoData().title == data.deletedTrackInfo.name) {
                player.stopVideo();
                player.loadVideoById("");
                progressBar.style.width = 0;
                thumb.hidden = true;
                thumb.src = "";
            }
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
    let playlist = document.querySelector(".playlist");
    playlist.innerHTML = "";
}

function updatePlaylist(newPlaylist, url = "") {
    clearPlaylist();
    let playlist = $(".playlist");
    if (newPlaylist.length === 0) {
        playlist.text("No tracks in playlist :(");
    }
    newPlaylist.forEach((track) => {
        let trackElement = $(`<div class="playlist__track"></div>`);
        let playButton = $(
            `<button class="track__playButton"><i class="fas fa-play"></i></button>`
        );
        let trackTitle = $(
            `<div class="track__title" data-title="${track.name}">${track.name}</div>`
        );
        let deleteButton = $(
            `<button class="track__deleteButton"><i class="fa-solid fa-trash-can"></i></button>`
        );
        let chosenUrl = "";
        try {
            chosenUrl = youtube_parser(url);
            let trackUrl = youtube_parser(track.url);
            if (chosenUrl === trackUrl) {
                playButton.addClass("track__playButton_active");
            }
        } catch (error) {
            console.log(error);
        }
        let trackData = {
            name: track.name,
            url: track.url,
        };
        let youtubeURL = "https://www.youtube.com/watch?v=" + chosenUrl;
        deleteButton.on("click", (e) => {
            deleteTrack(e, trackData, youtubeURL);
        });
        playButton.on("click", (e) => {
            changeTrack(e, track);
        });
        trackElement.append(playButton, trackTitle, deleteButton);
        playlist.prepend(trackElement);
    });
}

function deleteTrack(event, trackData, chosenTrackUrl) {
    roomSocket.send(
        JSON.stringify({
            event: "DELETE_TRACK",
            message: "Delete track.",
            track: trackData,
            chosenTrackUrl: chosenTrackUrl,
        })
    );
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
            onError: onPlayerError,
        },
    });
}

function onPlayerReady(event) {
    audioPlayer.querySelector(".time .length").textContent = getTimeCodeFromNum(
        player.getDuration()
    );
    player.setVolume(50);
    mutePlayer();
    audioPlayer.querySelector(".name .title").textContent = player.getVideoData().title;

    // Set click listener to the whole page
    document.addEventListener("mouseup", firstClickListener);
    function firstClickListener(event) {
        if (isFirstClick) {
            isFirstClick = false;
            unMutePlayer();
            console.log("No longer muted!");
            document.getElementById("mute-msg").style.display = "none";
        }
    }

    connect();
}

function onPlayerError(event) {
    console.log("Player error.");
    console.log(event);
}

function onPlayerStateChange(event) {
    audioPlayer.querySelector(".time .length").textContent = getTimeCodeFromNum(
        player.getDuration()
    );
    audioPlayer.querySelector(".name .title").textContent = player.getVideoData().title;
}

//click on timeline to skip around
timeline.addEventListener(
    "click",
    (e) => {
        const timelineWidth = window.getComputedStyle(timeline).width;
        const timeToSeek = (e.offsetX / parseInt(timelineWidth)) * player.getDuration();
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
    progressBar.style.width = (player.getCurrentTime() / player.getDuration()) * 100 + "%";
    audioPlayer.querySelector(".time .current").textContent = getTimeCodeFromNum(
        player.getCurrentTime()
    );
}, 100);

//toggle between playing and pausing on button click
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
    return `${String(hours).padStart(2, 0)}:${minutes}:${String(seconds % 60).padStart(2, 0)}`;
}

function youtube_parser(url) {
    var code = url.match(/v=([^&#]{5,})/);
    return typeof code[1] == "string" ? code[1] : false;
}

function addTrack() {
    const id = youtube_parser(urlField.value);
    fetch(
        "https://www.googleapis.com/youtube/v3/videos?part=snippet&id=" + id + "&key=" + ytApiKey
    ).then((response) =>
        response.json().then((data) => {
            let youtubeURL = "https://www.youtube.com/watch?v=" + id;
            let title = data.items[0].snippet.title;
            if (id) {
                roomSocket.send(
                    JSON.stringify({
                        event: "ADD_TRACK",
                        url: youtubeURL,
                        name: title,
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
            urlField.value = "";
        })
    );
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

function setThumbnail(id) {
    fetch(
        "https://www.googleapis.com/youtube/v3/videos?part=snippet&id=" + id + "&key=" + ytApiKey
    ).then((response) =>
        response.json().then((data) => {
            let url = data.items[0].snippet.thumbnails.default.url;
            thumb.src = url;
            thumb.hidden = false;
        })
    );
}

function showContent() {
    $(".loading").addClass("hidden");
    $(".content").removeClass("hidden");
}
