import { useState, useEffect} from 'react'
import './App.css'
import './map/MapContainer'
import provinceIds from './data/province_id.json';
import MapContainer from './map/MapContainer';
import { fetchAiSummary, getMarkers } from './ApiService';
import AISummary from './AiSummary';

function App() {
  const [selectedDate, setSelectedDate] = useState(null)
  const [province, setProvince] = useState(null)
  const [markersData, setMarkersData] = useState(null);
  const [aiSummary, setAiSummary] = useState(null);
  const [loadingAiSummary, setLoadingAiSummary] = useState(false);
  const [loadingMarkers, setLoadingMarkers] = useState(false);

  const observationDates = [
      new Date(2025, 10, 10),
      new Date(2025, 10, 14)
  ];


  // setup at the beginning
  useEffect(() => {
    // select latest observation date based on get request result else
    const today = new Date();
    setSelectedDate(today)


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



  return (
      <div className="min-h-screen flex flex-col">
        {/* Header */}
        <header className="bg-blue-600 text-white p-4 min-h-20">
          <div className="container mx-auto">
          </div>
        </header>

        {/* Main content container */}
        <main className="flex-grow container mx-auto p-4">
          <div className="flex flex-col lg:flex-row gap-4">
            {/* Map container*/}
            <div className="flex-3 lg:w-2/1 max-w-[1000px] max-h-[700px] bg-green-100 p-6 rounded-lg aspect-square">
              <MapContainer markersData={markersData} setProvince={setProvince} province={province} selectedDate={selectedDate} setSelectedDate={setSelectedDate} observationDates={observationDates}/>
            </div>

            {/* Summary container */}
            <div className="flex-1 bg-yellow-100 p-6 rounded-lg">
              <AISummary fetchAiSummary={fetchAiSummary} setAiSummary={setAiSummary} setLoadingAiSummary={setLoadingAiSummary} loadingAiSummary={loadingAiSummary}/>
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
