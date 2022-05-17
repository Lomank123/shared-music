const sidebar = document.getElementById("collapse-sidebar");
const overlay = document.querySelector(".overlay");

function openNav() {
    sidebar.style.left = "0";
    overlay.classList.add("blur");
}

function closeNav() {
    sidebar.style.left = "-250px";
    overlay.classList.remove("blur");
}
