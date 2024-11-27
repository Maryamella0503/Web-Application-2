document.addEventListener("DOMContentLoaded", function() {
    var map = L.map('map').setView([51.505, -0.09], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 18,
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    // Initialize heatmap points
    var heatmapPoints = []; // Empty array initially

    // Heatmap layer setup
    var heatmapLayer = L.heatLayer(heatmapPoints, {
        radius: 25,
        blur: 15,
        maxZoom: 17
    }).addTo(map);

    // Fetch crime data from your API
    function loadCrimeData() {
        fetch('/api/crime-data')
            .then(response => response.json())
            .then(data => {
                console.log("Fetched data:", data);

                heatmapPoints = data.map(crime => {
                    let latitude = parseFloat(crime.latitude);
                    let longitude = parseFloat(crime.longitude);

                    if (isNaN(latitude) || isNaN(longitude)) {
                        console.error('Invalid coordinates:', crime);
                        return null;
                    }

                    return [latitude, longitude, 1];
                }).filter(point => point !== null);

                console.log("Heatmap points:", heatmapPoints);

                // Update the heatmap layer with the new points
                heatmapLayer.setLatLngs(heatmapPoints);
            })
            .catch(error => {
                console.error('Error fetching crime data:', error);
                alert('Failed to load crime data.');
            });
    }

    loadCrimeData(); // Call the function to load crime data
});

