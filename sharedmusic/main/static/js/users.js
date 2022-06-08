const username = $("#user").attr("username");
const usersList = document.getElementById("users-list");
let hostUsername = $("#host").attr("host_username");
let users = [];
let muteList = [];
let banList = [];

function updateUserList(users) {
    $(".room-title").text(`${hostUsername}'s room`);
    while (usersList.hasChildNodes()) {
        usersList.removeChild(usersList.firstChild);
    }
    users.forEach((user) => {
        let node = $(
            `<li>` + `<div class="online"></div>` + `<div class="username">${user.username}</div>` + `</li>`
        );
        if (user.username != hostUsername && username == hostUsername) {
            let muteOption = muteList.includes(user.username)
                ? `<a href="javascript:void(0)" onclick="unmuteUser('${user.username}')">Unmute user</a>`
                : `<a href="javascript:void(0)" onclick="muteUser('${user.username}')">Mute user</a>`;
            let dropdownButton = $(`
            <div onmouseover="dropdownHover(this)" class="dropdown">
                <button class="dropbtn"><i class="fa-regular fa-square-caret-down"></i></button>
                <div class="dropdown-content">
                    <a href="javascript:void(0)" onclick="changeHost('${user.username}')">Change host</a>` +
                    muteOption
                    + `<a href="javascript:void(0)" onclick="banUser('${user.username}')">Ban user</a>
                </div>
            </div>`
            );
            node.append(dropdownButton);
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

function banUser(username) {
    roomSocket.send(
        JSON.stringify({
            event: "BAN_USER",
            message: "Ban user.",
            username: username,
        })
    );
}

function unbanUser(username) {
    roomSocket.send(
        JSON.stringify({
            event: "UNBAN_USER",
            message: "Unban user.",
            username: username,
        })
    );
}

function handleUserBan() {
    $(".content").addClass("hidden");
    $(".loading").removeClass("hidden");
    $(".lds-ripple").text("");
    $(".loading__error").text("You have been banned from the room");
    let time = 10;
    $(".loading__message").text(`You will be redirected to home page in ${time} seconds`);
    let timerId = setInterval(() => {
        time -= 1;
        $(".loading__message").text(`You will be redirected to home page in ${time} seconds`);
    }, 1000);
    setTimeout(() => {
        clearInterval(timerId);
        window.location.href = "/";
    }, 10000);
}
