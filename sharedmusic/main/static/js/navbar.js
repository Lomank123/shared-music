const sidebar = document.getElementById("collapse-sidebar");
const main = document.getElementById("main");

function openNav() {
    sidebar.style.width = "250px";
    main.style.marginLeft = "250px";
}

function closeNav() {
    sidebar.style.width = "0";
    main.style.marginLeft = "0";
}
