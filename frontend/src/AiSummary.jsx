function AISummary({aiSummary , fetchAiSummary}) {



    return (
        <div className="p-6">
            <button onClick={fetchAiSummary} className="bg-green-200">Generate AI Summary</button>
            <h2 className="text-white text-2xl">AI Summary</h2>
            <p className="text-white">{aiSummary}</p>
        </div>
    );
}

export default AISummary;