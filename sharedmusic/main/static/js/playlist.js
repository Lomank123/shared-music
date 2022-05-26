const urlField = document.getElementById("url-field");
let currentTrack;
let hasVoted = false;

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
            $(".playlist-error").text("Track not found");
            setTimeout(() => {
                $(".playlist-error").text("");
            }, 5000);
        });
}

function handleVote() {
    if (hasVoted) {
        $("#vote-error").text("Already voted");
        setTimeout(() => {
            $("#vote-error").text("");
        }, 5000);
        return;
    }
    console.log("vote");
    votes += 1;
    let currentTrack = getCurrentTrackData();
    roomSocket.send(
        JSON.stringify({
            event: "VOTE_FOR_SKIP",
            message: "Vote",
            votes: votes,
            track: currentTrack,
        })
    );
    hasVoted = true;
}
