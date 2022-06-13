const chat = $("#chat");
const chatField = $("#chat-field");
let flag = false;

const options = {
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
};

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
    const text = chatField.val();
    if (text === "") {
        return;
    }
    roomSocket.send(
        JSON.stringify({
            event: "SEND_CHAT_MESSAGE",
            message: "New message incomming.",
            chat_message: text,
        })
    );
    chatField.val("");
}

function handleChatMessages(messages, reset = false) {
    if (reset) {
        chat.text("");
    }
    if (messages.length === 0) {
        chat.text("No messages :(");
        flag = true;
    // I need to remove "no messages :(" when first message arrives
    // Kinda bad implementation, maybe i should find a better way (someday)
    } else if (flag) {
        chat.text("");
        flag = false;
    }
    messages.forEach((newMessage) => {
        let date = new Date(newMessage.timestamp).toLocaleDateString("en-US", options);

        let message = $(`
        <div class="message">
            <div class="message__sender">${newMessage.username}</div>
            <div class="message__content">${newMessage.message}</div>
            <div class="message__time">${date}</div>
        </div>`);
        chat.append(message);
    });
}
