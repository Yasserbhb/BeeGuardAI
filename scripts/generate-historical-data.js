// Script to generate historical data for charts
const fetch = require('node-fetch');

async function generateHistoricalData() {
    const baseUrl = 'http://localhost:3000';

    // Get all ruches
    const ruchesResp = await fetch(`${baseUrl}/api/ruches`);
    const ruches = await ruchesResp.json();

    console.log(`Generating historical data for ${ruches.length} ruches...`);

    for (const ruche of ruches) {
        console.log(`\nGenerating data for ${ruche.nom}...`);

        // Generate 20 data points over the last 2 hours
        for (let i = 19; i >= 0; i--) {
            const baseTemp = 22 + Math.random() * 5;
            const baseHumidity = 55 + Math.random() * 15;

            const data = {
                ruche_id: ruche.id,
                nombre_frelons: Math.floor(Math.random() * (ruche.nom.includes('Jussieu 01') ? 8 : 4)),
                nombre_abeilles_entrees: Math.floor(Math.random() * 40) + 40,
                nombre_abeilles_sorties: Math.floor(Math.random() * 40) + 35,
                temperature: baseTemp.toFixed(1),
                humidite: baseHumidity.toFixed(1),
                etat_abeilles: Math.random() > 0.8 ? 'affaiblies' : 'normal',
                etat_acoustique: Math.random() > 0.9 ? 'stress' : 'normal'
            };

            try {
                await fetch(`${baseUrl}/api/donnees`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                console.log(`  ✓ Data point ${20 - i}/20`);
            } catch (err) {
                console.error(`  ✗ Error:`, err.message);
            }

            // Small delay to avoid overwhelming the server
            await new Promise(resolve => setTimeout(resolve, 100));
        }
    }

    console.log('\n✓ Historical data generation complete!');
}

generateHistoricalData().catch(console.error);
