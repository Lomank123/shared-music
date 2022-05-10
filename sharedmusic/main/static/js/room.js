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
let loop = false;
// Indicates whether user has clicked on window
isFirstClick = true;
const ytApiKey = "AIzaSyCp-e6T1qe6QqgjH6JydzBHCjB2raF6FrE";
const youtubeRawLink = "https://www.youtube.com/watch?v=";

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
        const loading = $(".loading");
        const content = $(".content");
        // If connection error occured while in the room
        if (loading.hasClass("hidden")) {
            content.addClass("hidden");
            loading.removeClass("hidden");
        }
        $(".loading__message").text("");
        $(".loading__error").text("Connection lost... Trying to reconnect");
    };

    roomSocket.onclose = (e) => {
        if (e.code === 1006) {
            // reconnect in 5 secs (player will be reloaded correctly)
            setTimeout(function () {
                connect();
            }, 5000);
        }
        pauseTrack();
    };

    roomSocket.onmessage = (e) => {
        let data = JSON.parse(e.data);
        data = data["payload"];
        console.log(data);

        if (data.event == "CONNECT") {
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
                    loop: loop,
                })
            );
        }
        if (data.event == "DISCONNECT") {
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
            if (data.loop) {
                $(".repeat-btn").children().toggleClass("repeat-active");
                loop = data.loop;
            }
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
        if (data.event == "CHANGE_LOOP") {
            $(".repeat-btn").children().toggleClass("repeat-active");
            loop = !loop;
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
        let youtubeURL = youtubeRawLink + chosenUrl;
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
    if (localStorage.getItem("volume") === null) {
        player.setVolume(50);
        localStorage.setItem("volume", 50);
    } else {
        player.setVolume(localStorage.getItem("volume"));
    }
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

    //click on timeline to skip around
    timeline.addEventListener("click", (e) => {
        const timelineWidth = window.getComputedStyle(timeline).width;
        const timeToSeek = (e.offsetX / parseInt(timelineWidth)) * player.getDuration();
        //player.seekTo(timeToSeek);
        roomSocket.send(
            JSON.stringify({
                event: "CHANGE_TIME",
                time: timeToSeek,
                message: "Change time.",
            })
        );
    });

    //hover over timeline to see time in current mouse position
    timeline.addEventListener("mousemove", (e) => {
        const timelineWidth = window.getComputedStyle(timeline).width;
        const timeToSeek = (e.offsetX / parseInt(timelineWidth)) * player.getDuration();
        let tooltip = $(".progress-tooltip");
        tooltip.text(getTimeCodeFromNum(timeToSeek));
        tooltip.get(0).style.left =
            e.pageX + tooltip.get(0).clientWidth + 15 < document.body.clientWidth
                ? e.pageX + 10 + "px"
                : document.body.clientWidth - tooltip.get(0).clientWidth - 5 + "px";
    });

    //click (or hold) volume slider to change volume
    volumeSlider.addEventListener("input", (e) => {
        renderVolumeSlider();
        newVolume = volumeSlider.value;
        player.setVolume(newVolume);
        localStorage.setItem("volume", newVolume);
        if (newVolume == 0) {
            mutePlayer();
        } else if (player.isMuted() && newVolume != 0) {
            // Just change the icon and unmute
            player.unMute();
            volumeEl.classList.add("icono-volumeMedium");
            volumeEl.classList.remove("icono-volumeMute");
        }
    });

    //check audio percentage and update time accordingly
    setInterval(() => {
        progressBar.style.width = (player.getCurrentTime() / player.getDuration()) * 100 + "%";
        audioPlayer.querySelector(".time .current").textContent = getTimeCodeFromNum(
            player.getCurrentTime()
        );
    }, 100);

    //toggle between playing and pausing on button click
    playBtn.addEventListener("click", () => {
        if (player.getPlayerState() === 1) {
            //pauseTrack();
            roomSocket.send(
                JSON.stringify({
                    event: "PAUSE",
                    message: "Track is now paused.",
                })
            );
        } else {
            //playTrack();
            roomSocket.send(
                JSON.stringify({
                    event: "PLAY",
                    message: "Track is now playing",
                })
            );
        }
    });

    audioPlayer.querySelector(".volume-button").addEventListener("click", () => {
        if (!player.isMuted()) {
            mutePlayer();
        } else {
            unMutePlayer();
        }
    });

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

    // If track in on loop, send CHANGE_TRACK event with the same track
    if (event.data == YT.PlayerState.ENDED && username == users[0].username && loop) {
        const id = youtube_parser(player.getVideoUrl());
        const trackData = {
            url: youtubeRawLink + id,
            name: player.getVideoData().title,
        };
        changeTrack(event, trackData);
        return;
    }

    // For now only host can send this event otherwise it will cause error
    // The event will be sent from all listeners and in some cases title will not be loaded
    if (event.data == YT.PlayerState.ENDED && username == users[0].username) {
        const id = youtube_parser(player.getVideoUrl());
        const trackData = {
            url: youtubeRawLink + id,
            name: player.getVideoData().title,
        };
        roomSocket.send(
            JSON.stringify({
                event: "TRACK_ENDED",
                message: "Track has ended. Need new one.",
                track: trackData,
            })
        );
    }
}

function mutePlayer() {
    player.mute();
    // Change the volume percentage to zero
    //audioPlayer.querySelector(".controls .volume-percentage").style.width = 0;
    volumeSlider.value = 0;
    renderVolumeSlider();
    volumeEl.classList.remove("icono-volumeMedium");
    volumeEl.classList.add("icono-volumeMute");
}

function unMutePlayer() {
    player.unMute();
    // Restore the volume percentage as it was before mute
    let newVolume = player.getVolume();
    if (newVolume == 0) {
        // Restore to default value it was zero
        newVolume = 50;
        player.setVolume(50);
    }
    volumeSlider.value = newVolume;
    renderVolumeSlider();
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
    let regExp = /^.*(youtu\.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#\&\?]*).*/;
    let match = url.match(regExp);
    if (match && match[2].length == 11) {
        return match[2];
    } else {
        return "";
    }
}

function addTrack() {
    const id = youtube_parser(urlField.value);
    fetch("https://www.googleapis.com/youtube/v3/videos?part=snippet&id=" + id + "&key=" + ytApiKey)
        .then((response) => response.json())
        .then((data) => {
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
        .catch((err) => {
            console.log(`Track with id=${id} not found`);
            $(".playlist-error").text("Track not found");
            setTimeout(() => {
                $(".playlist-error").text("");
            }, 5000);
        });
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
    fetch("https://www.googleapis.com/youtube/v3/videos?part=snippet&id=" + id + "&key=" + ytApiKey)
        .then((response) => response.json())
        .then((data) => {
            let url = data.items[0].snippet.thumbnails.default.url;
            thumb.src = url;
            thumb.hidden = false;
        })
        .catch((err) => {
            console.log(`Failed to get video thumbnail from id=${id}`);
        });
}

function showContent() {
    $(".loading").addClass("hidden");
    $(".content").removeClass("hidden");
}

function copyLinkToClipboard(btn) {
    navigator.clipboard.writeText(window.location.href);
    btn.textContent = "Copied to clipboard";
    setTimeout(() => {
        btn.textContent = "Copy link";
    }, 4000);
}

function renderVolumeSlider() {
    const min = volumeSlider.min;
    const max = volumeSlider.max;
    const value = volumeSlider.value;
    volumeSlider.style.backgroundSize = ((value - min) * 100) / (max - min) + "% 100%";
}

function changeLoop() {
    roomSocket.send(
        JSON.stringify({
            event: "CHANGE_LOOP",
            message: "Loop settings changed",
        })
    );
}
