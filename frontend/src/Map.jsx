import { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import geoJSONfinland from './data/fi.json';
import geoJSONbalticsea from './data/balticsea.json';
import mergedGeoJSON from './data/map.json';
import markersData from './data/markers.json';

function Map({ selectedDate, setSelectedDate }) {
    const mapRef = useRef(null);
    const firstClickDone = useRef(false);
    const zoomOutControlRef = useRef(null);
    const currentMarkersRef = useRef([]);
    const leafletZoomControlRef = useRef(null);
    const leafletZoomAddedRef = useRef(false);

    useEffect(() => {
        if (document.getElementById("map") && document.getElementById("map")._leaflet_id) {
            document.getElementById("map")._leaflet_id = null;
        }

        const updateMapText = (text) => {
            const el = document.getElementById("map-text");
            if (el) el.textContent = text;
        };

        // Initialize map
        const map = L.map("map", {
            center: [65.0, 26.0],
            zoom: 5.4,
            minZoom: 5.4,
            maxZoom: 15,
            maxBounds: [[55, 15], [75, 35]],
            maxBoundsViscosity: 1,
            scrollWheelZoom: false,
            doubleClickZoom: false,
            dragging: false,
            touchZoom: false,
            wheelPxPerZoomLevel: 30,
            zoomAnimation: false,
            fadeAnimation: false,
            markerZoomAnimation: false,
            attributionControl: false
        });

        mapRef.current = map;

        // Piilota Leafletin zoom-control alussa
        setTimeout(() => {
            const leafletZoom = document.querySelector(".leaflet-control-zoom");
            if (leafletZoom) leafletZoom.style.display = "none";
        }, 100);

        const hideMarkers = () => {
            currentMarkersRef.current.forEach((marker) => {
                map.removeLayer(marker);
            });
            currentMarkersRef.current = [];
        };

        // Zoom handling
        map.on("zoomend", () => {
            const isAtMinZoom = map.getZoom() <= 5.4;

            // Update on-screen text
            if (isAtMinZoom) {
                updateMapText("Select region");
            }

            // Toggle custom Zoom Out button
            if (zoomOutControlRef.current) {
                const btn = document.querySelector(".zoom-out-button");
                if (btn) btn.style.display = isAtMinZoom ? "none" : "block";
            }

            // Toggle Leaflet zoom control
            const leafletZoom = document.querySelector(".leaflet-control-zoom");
            if (leafletZoom) leafletZoom.style.display = isAtMinZoom ? "none" : "block";

            if (isAtMinZoom) {
                hideMarkers();
                const currentCenter = map.getCenter();
                if (currentCenter.lat !== 65.0 || currentCenter.lng !== 26.0) {
                    map.setView([65.0, 26.0], 5.4, { animate: false });
                }
            }

            try {
                map.options.touchZoom = !isAtMinZoom;
                if (map.touchZoom) {
                    if (isAtMinZoom) map.touchZoom.disable();
                    else map.touchZoom.enable();
                }
            } catch (e) {}
        });

        // Enable map interaction after first click
        const enableMapInteraction = () => {
            map.options.scrollWheelZoom = true;
            map.options.doubleClickZoom = true;
            map.options.dragging = true;
            map.options.touchZoom = true;
            map.scrollWheelZoom.enable();
            map.doubleClickZoom.enable();
            map.dragging.enable();
            map.touchZoom.enable();
        };

        // Custom zoom-out button
        const ZoomOutControl = L.Control.extend({
            onAdd: function (mapInstance) {
                const btn = L.DomUtil.create("button", "zoom-out-button");
                btn.innerHTML = "Zoom out";
                btn.style.padding = "8px 12px";
                btn.style.minWidth = "100px";
                btn.style.background = "#000";
                btn.style.color = "#fff";
                btn.style.border = "2px solid #00d4ff";
                btn.style.borderRadius = "8px";
                btn.style.cursor = "pointer";
                btn.onclick = () => {
                    hideMarkers();
                    updateMapText("Select region");
                    mapInstance.setView([65.0, 26.0], 5.4, { animate: true });
                };
                L.DomEvent.disableClickPropagation(btn);
                return btn;
            },
            onRemove: function () {}
        });

        // BASE TILE
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(map);

        // WORLD MASK
        const worldCoords = [
            [90, -180],
            [90, 180],
            [-90, 180],
            [-90, -180]
        ];
        const allHoles = [];
        mergedGeoJSON.features.forEach((feature) => {
            const processPolygon = (coords) => {
                const boundary = coords[0].map((coord) => [coord[1], coord[0]]);
                allHoles.push(boundary);
            };
            if (feature.geometry.type === "MultiPolygon") {
                feature.geometry.coordinates.forEach((polygon) => processPolygon(polygon));
            } else if (feature.geometry.type === "Polygon") {
                processPolygon(feature.geometry.coordinates);
            }
        });
        const maskGeoJSON = {
            type: "Feature",
            geometry: {
                type: "Polygon",
                coordinates: [
                    [
                        [-180, 90],
                        [180, 90],
                        [180, -90],
                        [-180, -90],
                        [-180, 90]
                    ],
                    ...allHoles.map(hole => hole.map(([lat, lng]) => [lng, lat]))
                ]
            }
        };
        L.geoJSON(maskGeoJSON, {
            style: {
                color: "#000",
                fillColor: "#000",
                fillOpacity: 0.85,
                weight: 0
            },
            renderer: L.canvas()
        }).addTo(map);

        // FINLAND REGIONS
        L.geoJSON(geoJSONfinland, {
            style: {
                fillColor: "transparent",
                color: "#ffffff",
                weight: 2,
                opacity: 0.6
            },
            onEachFeature: (feature, layer) => {
                if (feature.properties?.name) {
                    layer.bindTooltip(feature.properties.name, {
                        permanent: false,
                        direction: "center",
                        className: "province-tooltip",
                        opacity: 0.9
                    });
                }
                layer.on({
                    mouseover: (e) => {
                        e.target.setStyle({
                            weight: 3,
                            color: "#00d4ff",
                            opacity: 1
                        });
                    },
                    mouseout: (e) => {
                        e.target.setStyle({
                            weight: 2,
                            color: "#ffffff",
                            opacity: 0.6
                        });
                    },
                    click: (e) => {
                        const bounds = e.target.getBounds();
                        map.fitBounds(bounds, {
                            padding: [50, 50],
                            maxZoom: map.getMaxZoom(),
                            animate: true,
                            duration: 0.5
                        });
                        hideMarkers();
                        const clickedProvince = feature.properties.name;
                        const provinceData = markersData.find((p) => p.nimi === clickedProvince);
                        let count = 0;
                        if (provinceData) {
                            provinceData.havainnot.forEach((havainto) => {
                                const marker = L.marker(havainto.koordinaatit)
                                    .addTo(map)
                                    .bindPopup(havainto.info);
                                currentMarkersRef.current.push(marker);
                            });
                            count = provinceData.havainnot.length;
                        }
                        updateMapText(`${clickedProvince}: ${count} observations`);
                        if (!firstClickDone.current) {
                            enableMapInteraction();
                            zoomOutControlRef.current = new ZoomOutControl({ position: "topleft" });
                            map.addControl(zoomOutControlRef.current);
                            leafletZoomAddedRef.current = true;
                            const zoomOutBtn = document.querySelector(".zoom-out-button");
                            if (zoomOutBtn) zoomOutBtn.style.display = map.getZoom() <= 5.4 ? "none" : "block";
                            const leafletZoom = document.querySelector(".leaflet-control-zoom");
                            if (leafletZoom) leafletZoom.style.display = map.getZoom() <= 5.4 ? "none" : "block";
                            firstClickDone.current = true;
                        }
                    }
                });
            }
        }).addTo(map);

        return () => {
            if (mapRef.current) {
                mapRef.current.remove();
                mapRef.current = null;
            }
        };
    }, []);

    return (
        <div style={{ position: "relative" }}>
            <div
                id="map-text"
                style={{
                    position: "absolute",
                    top: "10px",
                    left: "50%",
                    transform: "translateX(-50%)",
                    zIndex: 9999,
                    color: "white",
                    fontSize: "22px",
                    fontWeight: "600",
                    textShadow: "0 0 6px black",
                    pointerEvents: "none"
                }}
            >
                Select region
            </div>
            <div id="map" className="aspect-1/1 w-full rounded-2xl"></div>
            <div
                style={{
                    position: "absolute",
                    bottom: "10px",
                    left: "50%",
                    transform: "translateX(-50%)",
                    zIndex: 9999
                }}
            >
                <DatePicker selectedDate={selectedDate} setSelectedDate={setSelectedDate} />
            </div>
        </div>
    );
}

const DatePicker = ({ selectedDate, setSelectedDate }) => {
    const handleDateChange = (event) => {
        setSelectedDate(event.target.value);
    };

    return (
        <div className="flex items-center gap-2 p-2 bg-gray-100 rounded-lg">
            <label htmlFor="date-picker" className="text-gray-700 font-medium">
                Select date:
            </label>
            <input
                id="date-picker"
                type="date"
                value={selectedDate}
                onChange={handleDateChange}
                className="p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
        </div>
    );
};

export default Map;
