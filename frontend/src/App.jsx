import { useState, useEffect, use} from 'react'
import './App.css'
import './map/MapContainer'
import provinceIds from './data/province_id.json';
import MapContainer from './map/MapContainer';
import { fetchAiSummary, getMarkers, getAllObservationsDates, getAiSummaryByDay } from './ApiService';
import AISummary from './AiSummary';


function App() {
  const [selectedDate, setSelectedDate] = useState(null)
  const [observationDates, setAllObservationDates] = useState([])
  const [province, setProvince] = useState(null)
  const [markersData, setMarkersData] = useState(null);
  const [aiSummary, setAiSummary] = useState(null);
  const [aiDateSummary, setDateAiSummary] = useState(null);
  const [loadingAiSummary, setLoadingAiSummary] = useState(false);
  const [loadingDateAiSummary, setLoadingDateAiSummary] = useState(false);
  const [loadingMarkers, setLoadingMarkers] = useState(false);


  // setup at the beginning
  useEffect(() => {
    getAllObservationsDates(setAllObservationDates)
  }, []);




  // send post request for markers in selected province
  useEffect(() => {
    console.log('ARVO PÄIVITETTY:', selectedDate?.toISOString().split("T")[0], province)

    if (selectedDate && province) {
    /*        setmarkerQuery({
              date: "2025-07-02",
              province: "8" || null,
          }); */
          const data = {
            date: selectedDate.toISOString().split("T")[0], // format YYYY-MM-DD,
            province: provinceIds[province] || null,
          }
          getMarkers(setLoadingMarkers, setMarkersData, data)
      }
  }, [selectedDate, province]);


  useEffect(() => {
    if (aiDateSummary) {
        console.log('AI DATE SUMMARY CHANGED:', aiDateSummary);
        getAiSummaryByDay(setLoadingDateAiSummary, setDateAiSummary, aiDateSummary)
    }

  }, [aiDateSummary])
  

  return (
      <div className="min-h-screen flex flex-col">
        {/* Header */}
        <header className="bg-blue-600 text-white p-4 min-h-20">
          <div className="container mx-auto text-3xl font-bold">
            LAKE LOVERS
          </div>
        </header>

        {/* Main content container */}
        <main className="flex-grow container mx-auto p-4">
          <div className="flex flex-col lg:flex-row gap-4">
            {/* Map container*/}
            <div className="flex-3 lg:w-2/1 max-w-[1000px] max-h-[700px] bg-green-100 p-6 rounded-lg aspect-square">
              <MapContainer setDateAiSummary={setDateAiSummary} markersData={markersData} setProvince={setProvince} province={province} selectedDate={selectedDate} setSelectedDate={setSelectedDate} observationDates={observationDates}/>
            </div>

            {/* Summary container */}
            <div className="flex-1 bg-yellow-100 p-6 rounded-lg max-w-[400px]">
              <AISummary fetchAiSummary={fetchAiSummary} setAiSummary={setAiSummary} setLoadingAiSummary={setLoadingAiSummary} loadingAiSummary={loadingAiSummary} aiSummary={aiSummary} aiDateSummary={aiDateSummary} loadingDateAiSummary={loadingDateAiSummary}/>
            </div>
          </div>
        </main>

        {/* Footer */}
        <footer className="bg-gray-800 text-white p-4 mt-auto min-h-20">
        </footer>
      </div>
    );
  };



export default App;
