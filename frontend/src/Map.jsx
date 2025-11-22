import { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

import geoJSONfinland from './data/fi.json';
import geoJSONbalticsea from './data/balticsea.json';
import mergedGeoJSON from './data/map.json';
import markersData from './data/markers.json';



function Map() {
    const mapRef = useRef(null);
    const firstClickDone = useRef(false);
    const zoomOutControlRef = useRef(null);
    const currentMarkersRef = useRef([]); // tallenna kartalla olevat markerit
    const leafletZoomControlRef = useRef(null);
    const leafletZoomAddedRef = useRef(false);

    useEffect(() => {
        if (document.getElementById("map") && document.getElementById("map")._leaflet_id) {
            document.getElementById("map")._leaflet_id = null;
        }

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
            zoomControl: false,
            touchZoom: false,
            wheelPxPerZoomLevel: 30,
            zoomAnimation: false,
            fadeAnimation: false,
            markerZoomAnimation: false,
            attributionControl: false

        });

        mapRef.current = map;


        // Show/hide the zoom-out button depending on zoom level
        map.on("zoomend", () => {
            const isAtMinZoom = map.getZoom() <= 5.4;

            // Toggle custom Zoom Out button visibility
            if (zoomOutControlRef.current) {
                const btn = document.querySelector(".zoom-out-button");
                if (btn) btn.style.display = isAtMinZoom ? "none" : "block";
            }

            // If we're at the minimum zoom, hide any markers and reset view
            if (isAtMinZoom) {
                hideMarkers();
                // Palauta kartta alkuperäiseen keskipisteeseen
                const currentCenter = map.getCenter();
                if (currentCenter.lat !== 65.0 || currentCenter.lng !== 26.0) {
                    map.setView([65.0, 26.0], 5.4, { animate: false });
                }
            }

            // Disable or enable pinch-to-zoom (touch gestures) depending on zoom
            try {
                // reflect option for other code that checks map.options
                map.options.touchZoom = !isAtMinZoom;
                if (map.touchZoom) {
                    if (isAtMinZoom) {
                        map.touchZoom.disable();
                    } else {
                        map.touchZoom.enable();
                    }
                }
            } catch (e) {}

            // Toggle the default Leaflet zoom control (+/-)
            if (leafletZoomControlRef.current) {
                if (isAtMinZoom && leafletZoomAddedRef.current) {
                    try { map.removeControl(leafletZoomControlRef.current); } catch (e) {}
                    leafletZoomAddedRef.current = false;
                } else if (!isAtMinZoom && !leafletZoomAddedRef.current) {
                    try { map.addControl(leafletZoomControlRef.current); } catch (e) {}
                    leafletZoomAddedRef.current = true;
                }
            }
        });


        // Enable map interaction after first click
        const enableMapInteraction = () => {
            map.options.scrollWheelZoom = true;
            map.options.doubleClickZoom = true;
            map.options.dragging = true;
            map.options.touchZoom = true;
            // create and store the Leaflet zoom control so we can remove/add it later
            const zoomCtrl = L.control.zoom({ position: 'topleft' });
            leafletZoomControlRef.current = zoomCtrl;
            map.addControl(zoomCtrl);
            leafletZoomAddedRef.current = true;

            map.scrollWheelZoom.enable();
            map.doubleClickZoom.enable();
            map.dragging.enable();
            map.touchZoom.enable();
        };

        const hideMarkers = () => {
            currentMarkersRef.current.forEach((marker) => {
                map.removeLayer(marker);
            });
            currentMarkersRef.current = [];
        };

        // Custom Zoom Out control (defined here so it can use hideMarkers/map)
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
                    mapInstance.setView([65.0, 26.0], 5.4, { animate: true });
                };
                L.DomEvent.disableClickPropagation(btn);
                return btn;
            },
            onRemove: function () {}
        });


        // Base map layer
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            attribution:
                '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);

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
                    // World outer shell
                    [
                        [-180, 90],
                        [180, 90],
                        [180, -90],
                        [-180, -90],
                        [-180, 90]
                    ],
                    // Holes from your data (flipped back to long/lat form)
                    ...allHoles.map(hole =>
                        hole.map(([lat, lng]) => [lng, lat])
                    )
                ]
            }
        };

        L.geoJSON(maskGeoJSON, {
            style: {
                color: "#000000",
                fillColor: "#000000",
                fillOpacity: 0.85,
                weight: 0
            },
            renderer: L.canvas()   // estää välivilkahduksen
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

                        // Lisää uudet markkerit klikatulle maakunnalle
                        const clickedProvince = feature.properties.name;
                        const provinceData = markersData.find((p) => p.nimi === clickedProvince);
                        if (provinceData) {
                            provinceData.havainnot.forEach((havainto) => {
                            const marker = L.marker(havainto.koordinaatit)
                                .addTo(map)
                                .bindPopup(havainto.info);
                            currentMarkersRef.current.push(marker);
                            });
                        }

                        if (!firstClickDone.current) {
                            enableMapInteraction();
                            zoomOutControlRef.current = new ZoomOutControl({ position: "topleft" });
                            map.addControl(zoomOutControlRef.current);
                            const btn = document.querySelector(".zoom-out-button");
                            if (btn) btn.style.display = map.getZoom() <= 5.4 ? "none" : "block";
                            firstClickDone.current = true;
                        }
                        },
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
        <div>
            <div id="map" className="aspect-1/1 w-full rounded-2xl"></div>
        </div>
    );
}

export default Map;
