const http = require('http');

function makeRequest(data) {
    return new Promise((resolve, reject) => {
        const options = {
            hostname: 'localhost',
            port: 3000,
            path: '/api/donnees',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        };

        const req = http.request(options, (res) => {
            let body = '';
            res.on('data', (chunk) => body += chunk);
            res.on('end', () => resolve(body));
        });

        req.on('error', reject);
        req.write(JSON.stringify(data));
        req.end();
    });
}

async function generateWeekData() {
    console.log('Generating 7 days of historical data (1 point per hour)...\n');

    const ruches = [
        { id: 4, nom: 'Ruche St-Cyr 01', baseTemp: 23, baseFrelons: 1 },
        { id: 5, nom: 'Ruche Jussieu 01', baseTemp: 24, baseFrelons: 5 },
        { id: 6, nom: 'Ruche St-Cyr 02', baseTemp: 22, baseFrelons: 0 },
        { id: 7, nom: 'Ruche Jussieu 02', baseTemp: 25, baseFrelons: 0 }
    ];

    const now = Date.now();
    const oneHour = 60 * 60 * 1000;
    const hoursInWeek = 7 * 24; // 168 hours

    for (const ruche of ruches) {
        console.log(`Generating data for ${ruche.nom}...`);
        let count = 0;

        for (let i = hoursInWeek; i >= 0; i--) {
            // Time variation - more activity during day (8am-6pm)
            const hour = (24 - (i % 24)) % 24;
            const isDaytime = hour >= 8 && hour <= 18;
            const activityMultiplier = isDaytime ? 1.5 : 0.5;

            // Day of week variation - less activity on weekends
            const dayOfWeek = Math.floor(i / 24) % 7;
            const isWeekend = dayOfWeek === 0 || dayOfWeek === 6;
            const weekendMultiplier = isWeekend ? 0.7 : 1;

            // Temperature variation by time of day
            const tempVariation = Math.sin((hour / 24) * 2 * Math.PI) * 3;
            const temperature = (ruche.baseTemp + tempVariation + (Math.random() - 0.5) * 2).toFixed(1);

            // Humidity inverse to temperature
            const humidite = (70 - tempVariation * 2 + (Math.random() - 0.5) * 10).toFixed(1);

            // Frelons - more during daytime, spike around lunch time
            let nombreFrelons = ruche.baseFrelons;
            if (isDaytime) {
                nombreFrelons += Math.floor(Math.random() * 3);
                if (hour >= 11 && hour <= 14) { // Lunch spike
                    nombreFrelons += Math.floor(Math.random() * 2);
                }
            }

            // Bee activity - higher during day, varies by ruche health
            const baseActivity = ruche.id === 5 ? 40 : 80; // Ruche 5 is weakened
            const abeilles_entrees = Math.floor(
                baseActivity * activityMultiplier * weekendMultiplier + Math.random() * 30
            );
            const abeilles_sorties = Math.floor(
                abeilles_entrees * (0.9 + Math.random() * 0.2)
            );

            // État variations
            const etat_abeilles = ruche.id === 5 ?
                (Math.random() > 0.7 ? 'affaiblies' : 'normal') :
                (Math.random() > 0.95 ? 'affaiblies' : 'normal');

            const etat_acoustique = ruche.id === 5 ?
                (Math.random() > 0.7 ? 'stress' : 'normal') :
                (Math.random() > 0.9 ? 'stress' : 'normal');

            const data = {
                ruche_id: ruche.id,
                nombre_frelons: nombreFrelons,
                nombre_abeilles_entrees: abeilles_entrees,
                nombre_abeilles_sorties: abeilles_sorties,
                temperature: parseFloat(temperature),
                humidite: parseFloat(humidite),
                etat_abeilles: etat_abeilles,
                etat_acoustique: etat_acoustique
            };

            try {
                await makeRequest(data);
                count++;
                if (count % 24 === 0) {
                    console.log(`  ✓ ${count}/${hoursInWeek} data points generated`);
                }
            } catch (err) {
                console.error(`  ✗ Error at data point ${count}:`, err.message);
            }

            // Small delay to avoid overwhelming the server
            await new Promise(resolve => setTimeout(resolve, 10));
        }

        console.log(`  ✓ Completed: ${count} data points for ${ruche.nom}\n`);
    }

    console.log('✓ All historical data generation complete!');
    console.log('Total data points generated:', hoursInWeek * ruches.length);
}

generateWeekData().catch(console.error);
