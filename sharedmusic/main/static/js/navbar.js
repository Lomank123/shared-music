const sidebar = document.getElementById("collapse-sidebar");
const overlay = document.querySelector(".overlay");

function openNav() {
    sidebar.style.width = "250px";
    overlay.classList.add("blur");
}

function closeNav() {
    sidebar.style.width = "0";
    overlay.classList.remove("blur");
}
