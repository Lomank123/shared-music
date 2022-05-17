const ytApiKey = "AIzaSyCp-e6T1qe6QqgjH6JydzBHCjB2raF6FrE";
const youtubeRawLink = "https://www.youtube.com/watch?v=";
// Indicates whether user has clicked on window
isFirstClick = true;

// Notification settings
toastr.options = {
    closeButton: true,
    debug: false,
    newestOnTop: false,
    progressBar: true,
    positionClass: "toast-top-right",
    preventDuplicates: true,
    onclick: null,
    showDuration: "300",
    hideDuration: "1000",
    timeOut: "5000",
    extendedTimeOut: "1000",
    showEasing: "swing",
    hideEasing: "linear",
    showMethod: "fadeIn",
    hideMethod: "fadeOut",
};

function youtube_parser(url) {
    let regExp = /^.*(youtu\.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#\&\?]*).*/;
    let match = url.match(regExp);
    if (match && match[2].length == 11) {
        return match[2];
    } else {
        return "";
    }
}

function showContent() {
    $(".loading").addClass("hidden");
    $(".content").removeClass("hidden");
}

function copyLinkToClipboard(btn) {
    navigator.clipboard.writeText(window.location.href);
    btn.textContent = "Copied to clipboard";
    setTimeout(() => {
        btn.textContent = "Copy link";
    }, 4000);
}
