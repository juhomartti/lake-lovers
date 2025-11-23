function AISummary({fetchAiSummary, setAiSummary, setLoadingAiSummary, loadingAiSummary, aiSummary}) {

    return (
        <div className="p-6">
            <h2 className="text-black text-2xl">AI Summary</h2>
            {loadingAiSummary || <button onClick={() => fetchAiSummary(setLoadingAiSummary, setAiSummary )} className="bg-green-200 p-1 rounded-md mt-1">Generate AI Summary</button>}
            {!loadingAiSummary && <LoadingSpinner />}
             {aiSummary && <p className="text-black">{aiSummary}</p>}
        </div>
    )
}

export default AISummary;



function LoadingSpinner() {
  return (
    <>
      <style>
        {`
          .loader {
            margin-top: 10px;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: inline-block;
            border-top: 4px solid #F;
            border-right: 4px solid transparent;
            box-sizing: border-box;
            animation: rotation 1s linear infinite;
            position: relative;
          }

          .loader::after {
            content: '';
            box-sizing: border-box;
            position: absolute;
            left: 0;
            top: 0;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            border-left: 4px solid #FF3D00;
            border-bottom: 4px solid transparent;
            animation: rotation 0.5s linear infinite reverse;
          }

          @keyframes rotation {
            0% {
              transform: rotate(0deg);
            }
            100% {
              transform: rotate(360deg);
            }
          }
        `}
      </style>
      <span className="loader"></span>
      <p className="text-black inline-flex text-center">Loading summary...</p>
    </>
  );
}
