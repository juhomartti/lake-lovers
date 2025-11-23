import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import geoJSONfinland from '../data/fi.json';
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";



function LeafletMap({ markersData, setProvince, province, selectedDate, setSelectedDate, observationDates }) {
    const leafletMapRef = useRef(null); // store a mutable value that does not cause a re-render 
    const [infoText, setInfoText] = useState("Select Region")

    // let zoomControl = null


    useEffect(() => {
        // create leafletMap
        const leafletMap = L.map("leafletMap", {
            center: [65.0, 26.0],
            zoom: 5.4,
            minZoom: 5.4,
            maxZoom: 15,
            maxBounds: [[57, 17], [72, 33]],
            maxBoundsViscosity: 1,
            scrollWheelZoom: true,
            doubleClickZoom: false,
            dragging: true,
            touchZoom: false,
            wheelPxPerZoomLevel: 30,
            zoomAnimation: true,
            fadeAnimation: false,
            markerZoomAnimation: true,
            attributionControl: false,
            zoomControl: false
        });

        // add OpenStreetleafletMap
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            attribution: "© OpenStreetMap contributors",
        }).addTo(leafletMap);

        // fit this frame
        // leafletMap.fitBounds([[54, 19], [70, 32]]);

        // save to ref
        leafletMapRef.current = leafletMap;

        const zoomControl = L.control.zoom({ position: "topright" });
        zoomControl.addTo(leafletMapRef.current);

        // add region highligting
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
                                weight: 6,
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
                            leafletMap.fitBounds(bounds, {
                                padding: [50, 50],
                                maxZoom: leafletMap.getMaxZoom(),
                                animate: true,
                                duration: 0.5
                            });
                            
                             setTimeout(() => {
                                
                            }, 500);
                            // fire zoomend manually
                            //leafletMap.fire("zoomend"); 
                            

                            // update selected province
                            setProvince(feature.properties?.name)
                        }
                    });
                    
                }
            }
        }).addTo(leafletMap);

        // listen zoomend events
        leafletMap.on("zoomend", () => {
        const currentZoom = leafletMap.getZoom();

    });

        // remove leafletMap if element is removed
        return () => {
            if (leafletMap) { leafletMap.remove(); }
        };
    }, []);

    
    // add markers
    useEffect(() => {

        console.log("MARKER muutettu", province);

        if (leafletMapRef.current && markersData) {
            // remove old markers
            leafletMapRef.current.eachLayer((layer) => {
                if (layer instanceof L.Marker) {
                    leafletMapRef.current.removeLayer(layer);
                }
            });

            // add new markers
            markersData.forEach((markerData) => {
                console.log(markerData)
                const marker = L.marker([markerData.latitude, markerData.longitude])
                .addTo(leafletMapRef.current)
                .bindPopup(`
                    <div style="min-width: 200px;">
                        <strong>${markerData.location || "N/A"}</strong><br/>
                        Operator: ${markerData.operator || "N/A"}<br/>
                        Date: ${markerData.date || "N/A"}<br/>
                        Description: ${markerData.description || "N/A"}<br/>
                        Level: ${markerData.level != null ? markerData.level : "N/A"}<br/>
                        Upkeep: ${markerData.upkeep || "N/A"}<br/>
                        <button id="popup-button-${markerData.id}" style="
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
                    </div>
                `);

                // zoom to clicked marker
                marker.on("click", () => {
                    leafletMapRef.current.setView(
                        [markerData.latitude, markerData.longitude],
                        10,
                        { animate: true }
                    );
                });
            });
        }

        // update info text


        if (markersData?.length > 0 && selectedDate) {
            setInfoText(`${province}: ${markersData.length} observations on ${selectedDate?.toISOString().split("T")[0]}`)
        } else if (selectedDate) (
            setInfoText(`${province}: 0 observations on ${selectedDate?.toISOString().split("T")[0]}`)
        )


    }, [markersData]);

    return (
        <div className="w-full h-full relative">
            <div id="infotext" className="absolute top-5 left-1/2 transform -translate-x-1/2 
             z-[1000] bg-white/80 px-3 py-1 rounded shadow">{infoText}</div>
            <div id="leafletMap" className="w-full h-full"></div>
            <div className="absolute top-4 left-4 z-[1000]"><DatePicker
                selected={selectedDate}
                onChange={setSelectedDate}
                highlightDates={observationDates}  
                inline    // show calendar
            /></div>
             
        </div>
        
    )
    
}

export default LeafletMap;

