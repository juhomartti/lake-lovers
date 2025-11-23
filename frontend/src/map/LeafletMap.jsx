import { use, useEffect, useRef, useState } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import geoJSONfinland from '../data/fi.json';
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";



function LeafletMap({ markersData, setProvince, province, selectedDate, setSelectedDate, observationDates, setDateAiSummary }) {
    const leafletMapRef = useRef(null); // store a mutable value that does not cause a re-render 
    const [infoText, setInfoText] = useState("");
    const [isLoading, setIsLoading] = useState(true);


    const formattedObservationDates = observationDates?.map((item) => new Date(item.date));

// select latest date at the beginning and set infoText
useEffect(() => {
    if (observationDates && observationDates.length > 0) {
        const latestDate = new Date(
                Math.max(
                    ...observationDates.map((item) => new Date(item.date).getTime())
                )
            );
            setSelectedDate(latestDate);
            setIsLoading(false);

            const dateString = latestDate.toISOString().split("T")[0];
            const selectedDateObservations = observationDates.filter(
                (item) => item.date === dateString
            );
            console.log(selectedDateObservations, "selectedDateObservations");
            const count = selectedDateObservations?.length;
            setInfoText(`Finland: ${count} observations on ${dateString}`);
        }
    }, [observationDates, setSelectedDate]);



    // update infoText when selectedDate or province changes
    useEffect(() => {
        if (selectedDate) {
            const dateString = selectedDate.toISOString().split("T")[0];

            const filteredMarkers = markersData?.filter(
                (marker) => marker.date === dateString
            ) || [];

            if (province) {
                const count = filteredMarkers.length;
                setInfoText(`${province}: ${count} observations on ${dateString}`);
            }
            else {
                const selectedDateObservation = observationDates.find(
                    (item) => new Date(item.date).getTime() === selectedDate.getTime()
                );
                const count = selectedDateObservation?.count || 0;
                const dateString = selectedDate.toISOString().split("T")[0];
                
                setInfoText(`Finland: ${count} observations on ${dateString}`);
            }
        }
    }, [selectedDate, province, markersData]);


    // let zoomControl = null

    // create leafletMap
    useEffect(() => {
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
                            if (province !== feature.properties?.name) {
                                e.target.setStyle({
                                weight: 2,
                                color: "#ffffff",
                                opacity: 0.6
                            });
                            }
                            
                        },
                        click: (e) => {
                            const clickedProvince = feature.properties?.name;
                            
                            // Toggle: jos sama alue klikataan uudestaan, poista valinta
                            if (province === clickedProvince) {
                                setProvince(null);
                                // Zoomaa takaisin koko Suomeen
                                leafletMap.setView([65.0, 26.0], 5.4, {
                                animate: true,
                                duration: 0.5
                                
                            });
                        } else {
                            // Valitse uusi alue
                            setProvince(clickedProvince);
                            const bounds = e.target.getBounds();
                            leafletMap.fitBounds(bounds, {
                                padding: [50, 50],
                                maxZoom: leafletMap.getMaxZoom(),
                                animate: true,
                                duration: 0.5
                            });
                        }
                    }
                });
                
            }
        }
        }).addTo(leafletMap);

        // listen zoomend events
        leafletMap.on("zoomend", () => {
            const currentZoom = leafletMap.getZoom();
            if (currentZoom === leafletMap.getMinZoom()) {
                setProvince(null);
                // hide markers
                leafletMapRef.current.eachLayer((layer) => {
                if (layer instanceof L.Marker) {
                    leafletMapRef.current.removeLayer(layer);
                }

                console.log("ZOOMEND")


            });
            }

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
                            display: none;
                            onclick='cons'>
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

                    setDateAiSummary(JSON.stringify({
                        date: markerData.date,
                        lat: markerData.latitude.toString(),
                        lon: markerData.longitude.toString(),
                        name: markerData.location
                    }));
                });
            });
        }

    }, [markersData]);


    return (
        <div className="w-full h-full relative">
            <div id="infotext" className="absolute bottom-5 left-1/2 transform -translate-x-1/2 
             z-[1000] bg-white/80 px-3 py-1 rounded shadow">{infoText}</div>
            <div id="leafletMap" className="w-full h-full"></div>
            <div className="absolute top-4 left-4 z-[1000]">
                {isLoading ? (
                    <div className="w-64 h-64 bg-gray-100 rounded-lg flex items-center justify-center">
                        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
                    </div>
                ) : (
                    <DatePicker
                        selected={selectedDate}
                        onChange={setSelectedDate}
                        highlightDates={formattedObservationDates}
                        inline
                    />
                )}
            </div>
        </div>
    )
}
export default LeafletMap;

