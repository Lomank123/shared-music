const urlField = document.getElementById("url-field");

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

function updatePlaylist(newPlaylist, url = "") {
    clearPlaylist();
    let playlist = $(".playlist");
    if (newPlaylist.length === 0) {
        playlist.text("No tracks in playlist :(");
    }
    newPlaylist.forEach((track) => {
        let trackElement = $(`<div class="playlist__track"></div>`);
        let playButton = $(`<button class="track__playButton"><i class="fas fa-play"></i></button>`);
        let trackTitle = $(`<div class="track__title" data-title="${track.name}">${track.name}</div>`);
        let deleteButton = $(
            `<button class="track__deleteButton"><i class="fa-solid fa-trash-can"></i></button>`
        );
        let trackData = {
            name: track.name,
            url: track.url,
        };
        playButton.on("click", (e) => {
            changeTrack(e, track);
        });
        let chosenUrl = "";
        try {
            chosenUrl = youtube_parser(url);
            let trackUrl = youtube_parser(track.url);
            if (chosenUrl === trackUrl) {
                //playButton.addClass("track__playButton_active");
                playButton = $(`
                <div class="box">
                    <div class="line-1"></div>
                    <div class="line-2"></div>
                    <div class="line-3"></div>
                    <div class="line-4"></div>
                    <div class="line-5"></div>
                </div>`);
                playButton.on("click", (e) => {
                    if (player.getPlayerState() === 1) {
                        roomSocket.send(
                            JSON.stringify({
                                event: "PAUSE",
                                message: "Track is now paused.",
                            })
                        );
                    } else {
                        roomSocket.send(
                            JSON.stringify({
                                event: "PLAY",
                                message: "Track is now playing",
                            })
                        );
                    }
                });
            }
        } catch (error) {
            console.log(error);
        }
        let youtubeURL = youtubeRawLink + chosenUrl;
        deleteButton.on("click", (e) => {
            deleteTrack(e, trackData, youtubeURL);
        });
        trackTitle.hover(
            (e) => playlistTooltipHover(e, track.name),
            (e) => playlistTooltipUnhover(e)
        );
        trackElement.append(playButton, trackTitle, deleteButton);
        playlist.prepend(trackElement);
        // If track is paused, stop animation
        if (player.getPlayerState() === 2) {
            stopEqualizerAnimation();
        }
    });
}

function clearPlaylist() {
    let playlist = document.querySelector(".playlist");
    playlist.innerHTML = "";
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
            setPlaylistError("Track not found");
        });
}

const playlistTooltip = $(".playlist-tooltip");

function playlistTooltipHover(e, text) {
    playlistTooltip.text(text);
    playlistTooltip.css("opacity", 1);
    playlistTooltip.css("top", e.clientY - 50);
    playlistTooltip.css("left", document.body.clientWidth / 2 - 150);
}

function playlistTooltipUnhover(e) {
    playlistTooltip.text("");
    playlistTooltip.css("opacity", 0);
}

function setPlaylistError(error) {
    $(".playlist-error").text(error);
    setTimeout(() => {
        $(".playlist-error").text("");
    }, 5000);
}
