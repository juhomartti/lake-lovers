import { useState, useEffect} from 'react'
import './App.css'
import Map from './Map.jsx'

import axios from 'axios';
import provinceIds from './data/province_id.json';

function App() {

  // Aseta oletusarvoksi nykyinen päivä (YYYY-MM-DD)
  const [selectedDate, setSelectedDate] = useState(() => {
    const today = new Date();
    return today.toISOString().split("T")[0]; // Muotoile YYYY-MM-DD
  });

  const [province, setProvince] = useState(null)
  const [markersData, setMarkersData] = useState(null);
  const [postData, setPostData] = useState(null);
  const [data, setData] = useState(null);

  // Funktio GET-pyynnön tekemiseen
  const fetchData = async () => {
    try {
      const response = await axios.get(`https://esiintymispaikka/rest/api/data?date=${selectedDate}`);
      setData(response.data);
    } catch (error) {
      console.error("Virhe datan hakemisessa:", error);
    }
  };


  const sendData = async () => {
    try {
      console.log("Lähetettävä data:", postData);

      const response = await axios.post(
        "http://127.0.0.1:8000/api/province/",
        postData, // Lähetettävä JSON-data
        {
          headers: {
            "Content-Type": "application/json",
          },
        }
      );
      console.log("Vastaus palvelimelta:", response.data);
      setMarkersData(response.data);
      // Voit käsitellä vastauksen täällä, esimerkiksi päivittää tilan
    } catch (error) {
      console.error("Virhe datan lähettämisessä:", error);
    }
  }; 


  // Voit kutsua fetchData-funktiota esimerkiksi komponentin mountauksen yhteydessä tai tarvittaessa
  useEffect(() => {
      if (selectedDate && province) {
/*           setPostData({
              date: "2025-07-02",
              province: "8" || null,
          }); */
          setPostData({
              date: selectedDate,
              province: provinceIds[province] || null,
          });
      }
  }, [selectedDate, province]);

  // Lähetetään postData, kun se on asetettu
  useEffect(() => {
      if (postData) {
          sendData();
      }
  }, [postData]);

  useEffect(() => {
    console.log("Päivitety markersData:", markersData);
  }, [markersData]);


  return (
  <div className="h-screen w-screen flex flex-col bg-emerald-900"> 
    <div className="w-[95%] max-w-7xl mx-auto flex-1 flex-col mt-5">
      <div className='bg-red-600 flex rounded-2xl'>
        otsikko
      </div>
      <div className='flex w-full bg-black flex-1 overflow-y-auto'> 
        <div className='flex-2 bg-amber-200 rounded-2xl'>
          <Map selectedDate={selectedDate} 
          setSelectedDate={setSelectedDate}
          setProvince={setProvince}
          markersData={markersData}/>
        </div>
        <div className='flex-1 bg-amber-800 rounded-2xl'>
          ai kooste
        </div>
      </div>
      <footer className='h-[50px] bg-blue-400 shrink-0'>
        Footer
      </footer>
    </div>
  </div>
  );
}


export default App
