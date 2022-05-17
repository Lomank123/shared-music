// Player elements
const audioPlayer = document.querySelector(".audio-player");
const timeline = document.querySelector(".timeline");
const progressBar = document.querySelector(".progress");
const volumeEl = document.querySelector(".volume-container .volume");
const volumeSlider = document.querySelector(".controls .volume-slider");
const playBtn = document.querySelector(".controls .toggle-play");
const thumb = document.querySelector(".name .thumb");

let player;
let loop = false;

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
    audioPlayer.querySelector(".time .length").textContent = getTimeCodeFromNum(player.getDuration());
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
        audioPlayer.querySelector(".time .current").textContent = getTimeCodeFromNum(player.getCurrentTime());
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
    audioPlayer.querySelector(".time .length").textContent = getTimeCodeFromNum(player.getDuration());
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
