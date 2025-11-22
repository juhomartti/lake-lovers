import { useState } from 'react'
import './App.css'
import Map from './Map.jsx'

function App() {
  return (
    <div className="h-screen w-screen flex flex-col bg-emerald-900">
      <div className="w-[95%] max-w-7xl mx-auto h-auto
      bg-blue-500 flex flex-col
      mt-5">
        <div className='bg-red-600 flex rounded-2xl'>
          otsikko
        </div>
        <div className='flex w-full bg-black h-full'>
          <div className='flex-2 bg-amber-200 rounded-2xl h-full'>
            <Map />
          </div>
          <div className='flex-1 bg-amber-800 rounded-2xl h-full'>
            ai kooste
          </div>
        </div>
      </div>
    </div>
  );
}


export default App
