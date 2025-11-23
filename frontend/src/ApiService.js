import axios from 'axios';


    // ai summary fetch
export const fetchAiSummary = async (setLoadingAiSummary, setAiSummary) => {
    try {
        setLoadingAiSummary(true);
        const response = await axios.get(`http://127.0.0.1:8000/api/ai`);
        setAiSummary(response.data);
    } catch (error) {
        console.error("Virhe datan hakemisessa:", error);

    } finally {
        setLoadingAiSummary(false);
    }
}

    // post request for markers
export const getMarkers = async (setLoadingMarkers, setMarkersData, postData) => {
    try {
        setLoadingMarkers(true);
    
        if (postData.province != null) {
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
            setMarkersData([...response.data]);
        } else {
            console.log("Epäkelvollinen province, ei löydy id refrencestä")
            setMarkersData([]);
        }
        
    } catch (error) {
        console.error("Virhe datan lähettämisessä:", error);
        console.error("Virheen aiheuttaneet arvot:", postData);
    } finally {
        setLoadingMarkers(false)
    }
}




