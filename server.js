const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const axios = require('axios');

const app = express();
const server = http.createServer(app);
const io = socketIo(server);

app.use(express.static('public'));

let lastTimestamps = {};

async function fetchLatestData() {
    try {
        const res = await axios.get('http://api.thingspeak.com/channels/2271543/feeds/last.json?api_key=ALI9TEXYDHUM9BAZ');
        const data = res.data;
        const currentTimestamp = new Date().getTime(); // Current timestamp in milliseconds

        let beaconStatuses = {};

        for (let i = 1; i <= 10; i++) {
            if (data["field" + i] === "1") {
                beaconStatuses["beacon" + i] = "On";
                lastTimestamps["beacon" + i] = currentTimestamp; // Store the timestamp of the latest update
            } else if (!lastTimestamps["beacon" + i] || currentTimestamp - lastTimestamps["beacon" + i] > 12000) { 
                // If no timestamp exists for this beacon or it's been more than 12 seconds since the last update, set status to Off
                beaconStatuses["beacon" + i] = "Off";
            } else {
                beaconStatuses["beacon" + i] = "On"; 
                // If there's a recent timestamp (less than 12 seconds ago), it's still considered "On"
            }
        }

        return beaconStatuses;

    } catch (error) {
        console.error("Failed to fetch data:", error);
    }
}

setInterval(async () => {
    const latestStatuses = await fetchLatestData();
    io.emit('beaconStatuses', latestStatuses);
}, 10000);

const PORT = 3000;
server.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
});
