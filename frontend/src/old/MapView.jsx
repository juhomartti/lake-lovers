import { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import geoJSONfinland from '../data/fi.json';
import geoJSONbalticsea from '../data/balticsea.json';
import mergedGeoJSON from '../data/map.json';

function MapView({ selectedDate, setSelectedDate, setProvince, markersData }) {



    

    return (
        <>
            <div id="map" className="aspect-1/1 w-full rounded-2xl"></div>
        </>
    );
}

