import { useState } from 'react'
import './App.css'
import Map from './Map.jsx'

function App() {
  return (
    <div className="h-screen w-screen flex flex-col bg-emerald-900">
      <div className="w-[70%] h-screen mx-auto bg-blue-500 flex flex-col">
        <div className='bg-red-600 flex'>
          otsikko
        </div>
        <div className='flex h-full w-full bg-black'>
          <div className='flex-1 bg-amber-200 rounded-2xl'>
            <Map />
          </div>
          <div className='flex-1 bg-amber-800 rounded-2xl'>
            ai kooste
          </div>
        </div>
      </div>
    </div>
  );
}


export default App
