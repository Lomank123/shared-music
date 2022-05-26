let permissions = {};

let modal = $modal({
    title: "Change room permissions",
    content: `<div class="perms-menu"><div class="grid-wrapper" data="title">
        <div class="perms-menu__name">Permissions</div>
        <div class="perms-menu__option">Any user</div>
        <div class="perms-menu__option">Host only</div>
    </div>
    <div class="grid-wrapper" data="PAUSE">
        <div class="perms-menu__name">Pause track</div>
        <input type="radio" name="pause" value="1" class="perms-menu__option" />
        <input type="radio" name="pause" value="5" class="perms-menu__option" />
    </div>
    <div class="grid-wrapper" data="ADD_TRACK">
        <div class="perms-menu__name">Add track</div>
        <input type="radio" name="add" value="1" class="perms-menu__option" />
        <input type="radio" name="add" value="5" class="perms-menu__option" />
    </div>
    <div class="grid-wrapper" data="CHANGE_TIME">
        <div class="perms-menu__name">Change time</div>
        <input type="radio" name="change_time" value="1" class="perms-menu__option" />
        <input type="radio" name="change_time" value="5" class="perms-menu__option" />
    </div>
    <div class="grid-wrapper" data="CHANGE_TRACK">
        <div class="perms-menu__name">Change track</div>
        <input type="radio" name="change_track" value="1" class="perms-menu__option" />
        <input type="radio" name="change_track" value="5" class="perms-menu__option" />
    </div>
    <div class="grid-wrapper" data="DELETE_TRACK">
        <div class="perms-menu__name">Delete track</div>
        <input type="radio" name="delete" value="1" class="perms-menu__option" />
        <input type="radio" name="delete" value="5" class="perms-menu__option" />
    </div>
</div>`,
    footerButtons: [
        { class: "btn btn__ok", text: "Save", handler: "savePerms()" },
        { class: "btn btn__cancel", text: "Cancel", handler: "closeModal()" },
    ],
});

function showModal() {
    modal.show();
    let settings = $(".perms-menu").children();
    settings.each((idx, setting) => {
        setting = $(setting);
        if (setting.attr("data") == "title") {
            return;
        }
        let currentValue = permissions[setting.attr("data")];
        setting.find(`input[type="radio"][value="${currentValue}"]`).prop("checked", true);
    });
}
function closeModal() {
    modal.hide();
}
function savePerms() {
    if (username != hostUsername) {
        return;
    }
    let settings = $(".perms-menu").children();
    settings.each((idx, setting) => {
        setting = $(setting);
        if (setting.attr("data") == "title") {
            return;
        }
        let perm = setting.attr("data");
        let newValue = setting.find('input[type="radio"]:checked').val();
        permissions[perm] = newValue;
    });
    console.log("Permissions saved, boss");
    console.log(permissions);
    roomSocket.send(
        JSON.stringify({
            event: "CHANGE_PERMISSIONS",
            message: "Room permissions changed",
            permissions: permissions,
        })
    );
    modal.hide();
}

// Visual permission display
function setPermissions(permsList) {
    let dict = {
        PAUSE: "Pause track",
        ADD_TRACK: "Add track",
        CHANGE_TIME: "Change time",
        CHANGE_TRACK: "Change track",
        DELETE_TRACK: "Delete track",
    };
    let allow = 1;
    if (username === hostUsername) {
        allow = 5;
    }
    let permsBlock = $(".permissions");
    permsBlock.text("");
    for (perm in permsList) {
        let sign = '<i class="fa-solid fa-xmark"></i>';
        // if allowed
        if (permsList[perm] <= allow) {
            sign = '<i class="fa-solid fa-check"></i>';
        }
        let node = `<div>${dict[perm]}: ${sign}</div>`;
        permsBlock.append(node);
    }
}
