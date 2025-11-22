import { useEffect } from "react";
import L from "leaflet";
import geoJSONfinland from './data/fi.json'
import geoJSONbalticsea from './data/balticsea.json'
import mergedGeoJSON from './data/map.json'


function Map() {
    
    useEffect(() => {
        const map = L.map('map', {
        center: [65.0, 26.0],   // suomen keskikoordinaatit
        zoom: 5,                
        minZoom: 5,            
        maxZoom: 15,            
        maxBounds: [[59, 20], [70, 32]], // suomen likimääräinen rajaus
        scrollWheelZoom: true, 
        doubleClickZoom: true, 
        dragging: true,
        maxBoundsViscosity: 0.8,
        wheelPxPerZoomLevel: 30, // pienempi = nopeampi zoom 
        zoomAnimation: true,
        });

        // Lisää OpenStreetMap-taso
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);


        // Maailman ulkokehä
        const worldCoords = [
            [90, -180],
            [90, 180],
            [-90, 180],
            [-90, -180]
        ];

         const allHoles = [];

        mergedGeoJSON.features.forEach(feature => {
            const processPolygon = (coords) => {
                const boundary = coords[0].map(coord => [coord[1], coord[0]]);
                allHoles.push(boundary);
            };

            if (feature.geometry.type === "MultiPolygon") {
                feature.geometry.coordinates.forEach(polygon => {
                    processPolygon(polygon);
                });
            } else if (feature.geometry.type === "Polygon") {
                processPolygon(feature.geometry.coordinates);
            }
        });

        L.polygon([worldCoords, ...allHoles], {
            color: '#000000',
            fillColor: '#000000',
            fillOpacity: 0.8,
            weight: 0
        }).addTo(map);

       L.geoJSON(geoJSONfinland, {
            style: {
                fillColor: 'transparent',
                color: '#ffffff',
                weight: 2,
                opacity: 0.6
            },
            onEachFeature: (feature, layer) => {
                // Lisää tooltip maakunnan nimellä
                if (feature.properties && feature.properties.name) {
                    layer.bindTooltip(feature.properties.name, {
                        permanent: false,    // Näkyy vain hoverissa
                        direction: 'center', // Keskellä aluetta
                        className: 'province-tooltip',
                        opacity: 0.9
                    });
                }
                
                // Hover-efekti
                layer.on({
                    mouseover: (e) => {
                        e.target.setStyle({
                            weight: 3,
                            color: '#00d4ff',
                            opacity: 1
                        });
                    },
                    mouseout: (e) => {
                        e.target.setStyle({
                            weight: 2,
                            color: '#ffffff',
                            opacity: 0.6
                        });
                    }
                });
            }
        }).addTo(map);


        // Siivous funktio kartan poistamiseksi komponentin unmountissa
        return () => {
            map.remove();
        };
    }, []);


    return (
        <>
            <style>
                {`
                .leaflet-attribution-flag {
                    display: none !important;
                }
                .province-tooltip {
                    background-color: rgba(0, 0, 0, 0.85) !important;
                    border: 2px solid #00d4ff !important;
                    border-radius: 8px !important;
                    color: #ffffff !important;
                    font-size: 14px !important;
                    font-weight: 600 !important;
                    padding: 8px 12px !important;
                    box-shadow: 0 4px 12px rgba(0, 212, 255, 0.3) !important;
                }
                
                .province-tooltip::before {
                    display: none !important;
                }
                `}
            </style>
            <div>
                <div id="map" className="aspect-2/3 not-first:w-full rounded-2xl"></div>
            </div>
        </>
        );
    }

export default Map;