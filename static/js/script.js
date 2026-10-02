async function sendAlert() {

    const alertBox = document.getElementById("alertBox");
    const alertButton = document.getElementById("alertButton");

    if (!alertBox || !alertButton) {
        return;
    }

    alertButton.disabled = true;
    alertButton.innerText = "SENDING...";

    try {

        const response = await fetch("/send_alert", {
            method: "POST"
        });

        const data = await response.json();

        if (data.success) {

            alertBox.innerHTML =
                "🚨 <strong>EMERGENCY ALERT SENT</strong><br>" +
                "<small>" +
                data.message +
                "</small>";

            alertBox.classList.add("show");

            alert(
                "🚨 Emergency Alert Sent!\n\n" +
                "Alert has been recorded."
            );

        } else {

            alert("⚠️ " + data.message);

        }

    } catch (error) {

        alert(
            "❌ Unable to send alert. Please try again."
        );

    }

    setTimeout(function () {

        alertButton.disabled = false;
        alertButton.innerText = "SEND ALERT";

    }, 3000);

}
async function checkIn() {

    const checkinBox = document.getElementById("checkinBox");
    const safeButton = document.getElementById("safeButton");

    if (!checkinBox || !safeButton) {
        return;
    }

    safeButton.disabled = true;
    safeButton.innerText = "CHECKING...";

    try {

        const response = await fetch("/checkin", {
            method: "POST"
        });

        const data = await response.json();

        if (data.success) {

            checkinBox.innerHTML =
                "🛡️ <strong>I'M SAFE</strong><br>" +
                "<small>" +
                data.message +
                "</small>";

            checkinBox.classList.add("show");

            alert(
                "🛡️ Safety Check-in Successful!\n\n" +
                "Your safe status has been recorded."
            );

        } else {

            alert("⚠️ " + data.message);

        }

    } catch (error) {

        alert(
            "❌ Unable to record check-in. Please try again."
        );

    }

    setTimeout(function () {

        safeButton.disabled = false;
        safeButton.innerText = "I'M SAFE";

    }, 3000);

}