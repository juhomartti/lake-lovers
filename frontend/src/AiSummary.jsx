function AISummary({fetchAiSummary, setAiSummary, loadingAiSummary, aiSummary, aiDateSummary, loadingDateAiSummary, setLoadingAiSummary}) {

    return (
        <div className="p-2">
            <h2 className="text-black text-xl font-bold">AI Summary</h2>
            {loadingAiSummary || <button onClick={() => fetchAiSummary(setLoadingAiSummary, setAiSummary )} className="bg-green-200 p-1 rounded-md mt-1">Generate AI Summary</button>}
            {loadingAiSummary && <LoadingSpinner />}
             {aiSummary && <p className="text-black">{aiSummary}</p>}
            
             <div  className="text-black text-md mt-45 font-bold">AI Prediction for the observation:</div>
             {loadingDateAiSummary && <LoadingSpinner />}
             {aiDateSummary && <p className="text-black white-space: pre-wrap">{aiDateSummary}</p>}
             
        </div>
    )
}

export default AISummary;



function LoadingSpinner() {
  return (
    <>
      <div className="w-64 h-64 bg-gray-100 rounded-lg flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
      </div>
      <p className="text-black inline-flex text-center"></p>
    </>
  );
}
