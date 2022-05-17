const roomCode = $("#room").attr("room_code");
const protocol = window.location.protocol == "https:" ? "wss://" : "ws://";
const connectionString = protocol + window.location.host + "/ws/room/" + roomCode + "/";

let roomSocket = null;

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
            permissions = data.permissions;
            console.log(permissions);
            setPermissions(permissions);
            updateUserList(users);
            if (username === data.user) {
                updatePlaylist(data.playlist);
            }
        }
        if (data.event == "GET_TRACK_FROM_LISTENERS") {
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
                    event: "SEND_TRACK_TO_NEW_USER",
                    message: "Send track to new user.",
                    user: data.receiver,
                    track: trackData,
                    loop: loop,
                })
            );
        }
        if (data.event == "DISCONNECT") {
            users = data.listeners.users;
            updateUserList(users);
        }
        if (data.event == "ALREADY_CONNECTED") {
            roomSocket.close(1000, (reason = "qweqweqweS"));
            console.log("Closing connection. Refresh the page.");
        }
        if (data.event == "ADD_TRACK") {
            // display new track in playlist with buttons
            updatePlaylist(data.playlist, player.getVideoUrl());
        }
        if (data.event == "CHANGE_TRACK") {
            const id = youtube_parser(data.track.url);
            setThumbnail(id);
            player.loadVideoById(id);
            playTrack();
            updatePlaylist(data.playlist, data.track.url);
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
        if (data.event == "HOST_CHANGED") {
            $("#host").attr("host_username", data.new_host);
            hostUsername = $("#host").attr("host_username");
            updateUserList(users);
            setPermissions(permissions);
        }
        if (data.event == "CHANGE_PERMISSIONS") {
            permissions = data.permissions;
            setPermissions(permissions);
            toastr["info"]("Room permissions have been changed");
        }
        if (data.event == "ROOM_NOT_ALLOWED") {
            toastr["error"]("Insufficient permissions");
        }
    };

    if (roomSocket.readyState == WebSocket.OPEN) {
        roomSocket.onopen();
    }
}
