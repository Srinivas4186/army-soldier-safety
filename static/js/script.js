function sendAlert() {

    let alertBox = document.getElementById("alertBox");

    alertBox.innerHTML =
        "<h2>🚨 EMERGENCY ALERT SENT</h2>" +
        "<p>Command center has been notified.</p>";

    alertBox.style.marginTop = "30px";
}