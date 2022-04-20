const roomCode = $("#room").attr("room_code");
const connectionString =
    "ws://" + window.location.host + "/ws/room/" + roomCode + "/";
const roomSocket = new WebSocket(connectionString);
const username = $("#user").attr("username");
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
    console.log(e.reason);
  }

    roomSocket.onmessage = (e) => {
        let data = JSON.parse(e.data);
        data = data["payload"];
        console.log(data);
        if (data.event == "CONNECT" || data.event == "DISCONNECT") {
            console.log(data.message);
            document.getElementById("users-count").innerHTML =
                data.count.toString();
        }
    };
    console.log(roomSocket.readyState);
    if (roomSocket.readyState == WebSocket.OPEN) {
        roomSocket.onopen();
    }
}

connect();
