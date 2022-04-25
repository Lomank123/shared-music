const sidebar = document.getElementById("collapse-sidebar");
const main = document.getElementById("main");
const blur = document.getElementById("blur");

function openNav() {
    sidebar.style.width = "250px";
    //main.style.marginLeft = "250px";
}

function closeNav() {
    sidebar.style.width = "0";
    //main.style.marginLeft = "0";
}
