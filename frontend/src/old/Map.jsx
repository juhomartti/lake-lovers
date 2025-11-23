import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import geoJSONfinland from '../data/fi.json';
import geoJSONbalticsea from '../data/balticsea.json';
import mergedGeoJSON from '../data/map.json';

function Map({ selectedDate, setSelectedDate, setProvince, markersData }) {
    const mapRef = useRef(null);
    const firstClickDone = useRef(false);
    const zoomOutControlRef = useRef(null);
    const currentMarkersRef = useRef([]);
    const leafletZoomAddedRef = useRef(false);
    const clickedProvinceRef = useRef(null);
    const [clickedProvince, setClickedProvince] = useState(null);

    useEffect(() => {
    if (clickedProvince) {
            clickedProvinceRef.current = clickedProvince;
        }
    }, [clickedProvince]);

    const updateMapText = (text) => {
        const el = document.getElementById("map-text");
        if (el) el.textContent = text;
    };

    const hideMarkers = () => {
        currentMarkersRef.current.forEach((marker) => {
            if (mapRef.current) {
                mapRef.current.removeLayer(marker);
            }
        });
        currentMarkersRef.current = [];
    };

    const updateMarkers = () => {
        if (!mapRef.current || !markersData) return;

        hideMarkers();

        if (markersData.length > 0) {
            markersData.forEach((havainto) => {
                const marker = L.marker([havainto.latitude, havainto.longitude])
                    .addTo(mapRef.current)
                    .bindPopup(`
                        <strong>${havainto.location}</strong><br/>
                        Operator: ${havainto.operator}<br/>
                        Date: ${havainto.date}<br/>
                        Description: ${havainto.description}<br/>
                        Level: ${havainto.level}<br/>
                        Upkeep: ${havainto.upkeep}<br/>
                        <button id="popup-button-${havainto.id}" style="
                            background-color: #007bff;
                            color: white;
                            border: none;
                            margin-top: 8px;
                            padding: 8px 12px;
                            border-radius: 4px;
                            cursor: pointer;
                        ">
                            Read AI Prediction
                        </button>
                    `);
                currentMarkersRef.current.push(marker);
            });
            updateMapText(`${clickedProvinceRef.current}: ${markersData.length} observations`);
        } else {
            updateMapText(`${clickedProvinceRef.current}: 0 observations`);
        }
    };

    useEffect(() => {
        if (document.getElementById("map") && document.getElementById("map")._leaflet_id) {
            document.getElementById("map")._leaflet_id = null;
        }

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

        setTimeout(() => {
            const leafletZoom = document.querySelector(".leaflet-control-zoom");
            if (leafletZoom) leafletZoom.style.display = "none";
        }, 100);

        map.on("zoomend", () => {
            const isAtMinZoom = map.getZoom() <= 5.4;
            if (isAtMinZoom) {
                updateMapText("Select region");
            }
            if (zoomOutControlRef.current) {
                const btn = document.querySelector(".zoom-out-button");
                if (btn) btn.style.display = isAtMinZoom ? "none" : "block";
            }
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
            } catch (e) { }
        });

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
            onRemove: function () { }
        });

        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(map);

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
                            const clickedProvince = feature.properties.name;
                            if (clickedProvinceRef.current === clickedProvince) return;

                            hideMarkers();
                            clickedProvinceRef.current = clickedProvince;
                            setClickedProvince(clickedProvince);
                            
            
                            if (setProvince) {
                                setProvince(clickedProvince);
                                console.log("Valittu province:", clickedProvince);
                            }

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
            }
        }).addTo(map);

        return () => {
            if (mapRef.current) {
                mapRef.current.remove();
                mapRef.current = null;
            }
        };
    }, []);

    useEffect(() => {
        console.log("MarkersData updated:", markersData);
        updateMarkers();
    }, [markersData]);

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
