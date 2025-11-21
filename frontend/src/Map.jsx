import { useEffect } from "react";
import L from "leaflet";
import 'leaflet/dist/leaflet.css';


function Map() {
  useEffect(() => {
    const map = L.map("map").setView([51.505, -0.09], 13);

        L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap'
        }).addTo(map);

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
                `}
            </style>
            <div>
                <div id="map" className="h-full min-h-[400px] w-full"></div>
            </div>
        </>
        );
    }

export default Map;