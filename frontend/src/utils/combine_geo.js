import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Hae polku komentoriviparametrina
const tiedostoPolku = process.argv[2];

if (!tiedostoPolku) {
  console.error('❌ Anna tiedoston polku komentoriviparametrina:');
  console.log('   node yhdistaja.js C:\\täysi\\polku\\tiedostoon\\fi.json');
  process.exit(1);
}

if (!fs.existsSync(tiedostoPolku)) {
  console.error(`❌ Tiedostoa ei löydy: ${tiedostoPolku}`);
  process.exit(1);
}

console.log(`✅ Käytetään tiedostoa: ${tiedostoPolku}`);

// Lue tiedosto
const rawData = fs.readFileSync(tiedostoPolku, 'utf8');
const geoJsonData = JSON.parse(rawData);

function yhdistaAlueetUusillaNimilla(geoJsonData, yhdistelmät) {
  const tulos = JSON.parse(JSON.stringify(geoJsonData));
  
  yhdistelmät.forEach(yhdistelmä => {
    const { uusiNimi, alueet } = yhdistelmä;
    
    const yhdistettävätFeaturet = tulos.features.filter(feature => 
      alueet.includes(feature.properties.name)
    );
    
    const muutFeaturet = tulos.features.filter(feature => 
      !alueet.includes(feature.properties.name)
    );
    
    if (yhdistettävätFeaturet.length > 0) {
      const yhdistettyGeometry = yhdistaGeometriat(yhdistettävätFeaturet);
      
      const yhdistettyFeature = {
        type: "Feature",
        properties: {
          name: uusiNimi,
          combined: true,
          originalAreas: alueet
        },
        geometry: yhdistettyGeometry
      };
      
      tulos.features = [...muutFeaturet, yhdistettyFeature];
    }
  });
  
  return tulos;
}

function yhdistaGeometriat(features) {
  const kaikkiKoordinaatit = [];
  
  features.forEach(feature => {
    const geometry = feature.geometry;
    
    if (geometry.type === "Polygon") {
      kaikkiKoordinaatit.push(geometry.coordinates);
    } else if (geometry.type === "MultiPolygon") {
      kaikkiKoordinaatit.push(...geometry.coordinates);
    }
  });
  
  if (kaikkiKoordinaatit.length === 1) {
    return {
      type: "Polygon",
      coordinates: kaikkiKoordinaatit[0]
    };
  } else {
    return {
      type: "MultiPolygon",
      coordinates: kaikkiKoordinaatit
    };
  }
}

const yhdistelmät = [
  {
    uusiNimi: "Ostrobothnia",
    alueet: ["Ostrobothnia", "Central Ostrobothnia"]
  },
  {
    uusiNimi: "Häme", 
    alueet: ["Päijät-Häme", "Tavastia Proper"]
  },
  {
    uusiNimi: "Southeastern Finland", 
    alueet: ["South Karelia", "Kymenlaakso"]
  }
];

const yhdistettyData = yhdistaAlueetUusillaNimilla(geoJsonData, yhdistelmät);

// Tallenna samaan kansioon kuin lähdetiedosto
const tallennusPolku = path.join(path.dirname(tiedostoPolku), 'suomen_yhdistetyt_alueet.json');

fs.writeFileSync(
  tallennusPolku,
  JSON.stringify(yhdistettyData, null, 2)
);

console.log('✅ Tiedosto tallennettu: suomen_yhdistetyt_alueet.json');
console.log(`📊 Alkuperäisiä alueita: ${geoJsonData.features.length}`);
console.log(`📊 Yhdistettyjä alueita: ${yhdistettyData.features.length}`);