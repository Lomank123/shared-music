const roomCode = $("#room").attr("room_code");
const urlField = document.getElementById("url-field");
const audio_tag = document.getElementById("youtube");
const connectionString =
    "ws://" + window.location.host + "/ws/room/" + roomCode + "/";
const roomSocket = new WebSocket(connectionString);
const username = $("#user").attr("username");
const hostUsername = $("#host").attr("host_username");
// Need to give host username
let users = [];

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

        if (data.event == "CONNECT" || data.event == "DISCONNECT") {
            document.getElementById("users-count").innerHTML =
                data.count.toString();
            if (username === hostUsername) {
                const trackData = {
                    name: "Soundtrack",
                    url: audio_tag.src,
                    currentTime: audio_tag.currentTime,
                    isPaused: audio_tag.paused,
                };
                roomSocket.send(
                    JSON.stringify({
                        event: "NEW_USER_JOINED",
                        message: "New user joined.",
                        user: data.user,
                        track: trackData,
                    })
                );
            }
        }
        if (data.event == "CHANGE_TRACK") {
            console.log(data.track.name);
            audio_tag.src = data.track.url;
        }
        if (data.event == "SET_CURRENT_TRACK") {
            audio_tag.src = data.track.url;
            audio_tag.currentTime = data.track.currentTime;
            if (!data.track.isPaused) {
                audio_tag.play();
            }
        }
    };

    console.log(roomSocket.readyState);
    if (roomSocket.readyState == WebSocket.OPEN) {
        roomSocket.onopen();
    }
}

connect();

function changeSong() {
    const url = urlField.value;
    let audio_streams = {};
    fetch("http://localhost:8080/" + url).then((response) => {
        if (response.ok) {
            response.text().then((data) => {
                console.log(data);
                var regex =
                    /(?:ytplayer\.config\s*=\s*|ytInitialPlayerResponse\s?=\s?)(.+?)(?:;var|;\(function|\)?;\s*if|;\s*if|;\s*ytplayer\.|;\s*<\/script)/gmsu;

                data = data.split("window.getPageData")[0];
                data = data.replace("ytInitialPlayerResponse = null", "");
                data = data.replace(
                    "ytInitialPlayerResponse=window.ytInitialPlayerResponse",
                    ""
                );
                data = data.replace(
                    "ytplayer.config={args:{raw_player_response:ytInitialPlayerResponse}};",
                    ""
                );

                var matches = regex.exec(data);
                var data =
                    matches && matches.length > 1
                        ? JSON.parse(matches[1])
                        : false;

                console.log(data);

                var streams = [];

                if (data.streamingData) {
                    if (data.streamingData.adaptiveFormats) {
                        streams = streams.concat(
                            data.streamingData.adaptiveFormats
                        );
                    }

                    if (data.streamingData.formats) {
                        streams = streams.concat(data.streamingData.formats);
                    }
                } else {
                    return false;
                }

                streams.forEach(function (stream, n) {
                    var itag = stream.itag * 1,
                        quality = false;
                    console.log(stream);
                    switch (itag) {
                        case 139:
                            quality = "48kbps";
                            break;
                        case 140:
                            quality = "128kbps";
                            break;
                        case 141:
                            quality = "256kbps";
                            break;
                        case 249:
                            quality = "webm_l";
                            break;
                        case 250:
                            quality = "webm_m";
                            break;
                        case 251:
                            quality = "webm_h";
                            break;
                    }
                    if (quality) audio_streams[quality] = stream.url;
                });

                console.log(audio_streams);

                audio_tag.src =
                    audio_streams["256kbps"] ||
                    audio_streams["128kbps"] ||
                    audio_streams["48kbps"];
                
                if (audio_tag.src) {
                    console.log(audio_tag.src);
                    roomSocket.send(
                        JSON.stringify({
                            event: "CHANGE_TRACK",
                            url: audio_tag.src,
                            message: "Change track."
                        })
                    );
                } else {
                    roomSocket.send(
                        JSON.stringify({
                            event: "CHANGE_TRACK_ERROR",
                            message: "Could not find audio url.",
                        })
                    );
                }
            });
        }
    });
}
