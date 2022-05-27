const username = $("#user").attr("username");
const usersList = document.getElementById("users-list");
let hostUsername = $("#host").attr("host_username");
let users = [];

function updateUserList(users) {
    while (usersList.hasChildNodes()) {
        usersList.removeChild(usersList.firstChild);
    }
    users.forEach((user) => {
        let node = $(
            `<li>` + `<div class="online"></div>` + `<div class="username">${user.username}</div>` + `</li>`
        );
        if (user.username != hostUsername && username == hostUsername) {
            //let changeHostButton = $(`<button onClick="changeHost('${user.username}')">Change</button>`);
            let changeHostButton = $(`
            <div class="dropdown">
                <button class="dropbtn"><i class="fa-regular fa-square-caret-down"></i></button>
                <div class="dropdown-content">
                <a href="javascript:void(0)" onclick="changeHost('${user.username}')">Change host</a>
                <a href="javascript:void(0)" onclick="muteUser('${user.username}')">Mute user</a>
                <a href="javascript:void(0)" onclick="unmuteUser('${user.username}')">Unmute user</a>
                </div>
            </div>`);
            node.append(changeHostButton);
        }
        if (user.username == hostUsername) {
            let icon = '<i class="fa-solid fa-crown"></i>';
            node.append(icon);
        }
        $("#users-list").append(node);
    });
    // Hide all elements with attribute "host-only", if user is not host
    if (username == hostUsername) {
        $("[host-only]").css("visibility", "visible");
    } else {
        $("[host-only]").css("visibility", "hidden");
    }
}

function changeHost(newHost) {
    roomSocket.send(
        JSON.stringify({
            event: "CHANGE_HOST",
            message: "Change host.",
            new_host: newHost,
        })
    );
}

function muteUser(username) {
    roomSocket.send(
        JSON.stringify({
            event: "MUTE_LISTENER",
            message: "Mute user.",
            username: username,
        })
    );
}

function unmuteUser(username) {
    roomSocket.send(
        JSON.stringify({
            event: "UNMUTE_LISTENER",
            message: "Unmute user.",
            username: username,
        })
    );
}

function sendMessage() {
    const chatField = document.getElementById("chat-field");
    const text = chatField.value;
    roomSocket.send(
        JSON.stringify({
            event: "SEND_CHAT_MESSAGE",
            message: "New message incomming.",
            chat_message: text,
        })
    );
}