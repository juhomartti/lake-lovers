import './LeafletMap'
import LeafletMap from './LeafletMap';

function MapContainer({markersData, setProvince, province, selectedDate, setSelectedDate, observationDates}) {

    return (
        <div className='h-full w-full'>
            <LeafletMap markersData={markersData} setProvince={setProvince} province={province} selectedDate={selectedDate} setSelectedDate={setSelectedDate} observationDates={observationDates}/>
        </div>
    )
}

export default MapContainer;