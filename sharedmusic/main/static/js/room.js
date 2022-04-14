var roomCode = document.getElementById("room").getAttribute("room_code");
var connectionString = 'ws://' + window.location.host + '/ws/room/' + roomCode + '/';
var roomSocket = new WebSocket(connectionString);

function connect() {
  roomSocket.onopen = () => {
    console.log("WebSocket connection created.");
    roomSocket.send(JSON.stringify({
      event: "START",
      message: "Hello world!",
    }));
  }

  roomSocket.onclose = (e) => {
    console.log('Socket is closed. Reconnect will be attempted in 10 seconds.', e.reason);
    setTimeout(() => {
        connect();
    }, 10000);
  }

  roomSocket.onmessage = (e) => {
    let data = JSON.parse(e.data);
    data = data["payload"];
    console.log(data);
  }
  console.log(roomSocket.readyState);
  if (roomSocket.readyState == WebSocket.OPEN) {
    roomSocket.onopen();
  }
}

connect();
