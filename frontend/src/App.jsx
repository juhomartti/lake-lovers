import { useState } from 'react'
import './App.css'
import Map from './Map.jsx'

function App() {

  // Aseta oletusarvoksi nykyinen päivä (YYYY-MM-DD)
  const [selectedDate, setSelectedDate] = useState(() => {
    const today = new Date();
    return today.toISOString().split("T")[0]; // Muotoile YYYY-MM-DD
  });


  return (
  <div className="h-screen w-screen flex flex-col bg-emerald-900"> 
    <div className="w-[95%] max-w-7xl mx-auto flex-1 flex-col mt-5">
      <div className='bg-red-600 flex rounded-2xl'>
        otsikko
      </div>
      <div className='flex w-full bg-black flex-1 overflow-y-auto'> 
        <div className='flex-2 bg-amber-200 rounded-2xl'>
          <Map selectedDate={selectedDate} setSelectedDate={setSelectedDate}/>
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
