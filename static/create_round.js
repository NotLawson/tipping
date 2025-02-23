// JS for round creation page

function addMatch() {
    var match = document.getElementById("match").cloneNode(true);
    document.getElementById("matches").appendChild(match);
}