// JS for the create user page

function addChild() {
    var child = document.getElementById("child").cloneNode(true);
    document.getElementById("children").appendChild(child);
}

function addFlag() {
    var flag = document.getElementById("flag").cloneNode(true);
    document.getElementById("flags").appendChild(flag);
}