// CONFIGURATION - Change these if needed
const SERVER = 'http://localhost:3000';
const USER_EMAIL = 'demo@sorbonne.fr';
const USER_PASSWORD = 'demo123';
const ORG_NAME = 'Sorbonne Université - Campus Jussieu';

// Ruches to create
const RUCHES = [
    { nom: 'Ruche Jussieu 01', localisation: 'Toit Bâtiment 44 - Exposition Sud' },
    { nom: 'Ruche Jussieu 02', localisation: 'Jardin Botanique - Zone Protégée' },
    { nom: 'Ruche Jussieu 03', localisation: 'Terrasse Bibliothèque - Plein Soleil' },
    { nom: 'Ruche Pierre et Marie Curie', localisation: 'Campus PMC - Près de la Serre' }
];

let TOKEN = '';
let API_KEY = '';
let rucheIds = [];

// Generate realistic sensor data
function generateSensorData() {
    const hour = new Date().getHours();
    const isDay = hour >= 6 && hour <= 20;

    return {
        nombre_frelons: isDay ? Math.floor(Math.random() * 8) : Math.floor(Math.random() * 2),
        nombre_abeilles_entrees: isDay ? Math.floor(Math.random() * 50) + 20 : Math.floor(Math.random() * 5),
        nombre_abeilles_sorties: isDay ? Math.floor(Math.random() * 50) + 20 : Math.floor(Math.random() * 5),
        temperature: (Math.random() * 10 + 18).toFixed(1),
        humidite: (Math.random() * 20 + 50).toFixed(1),
        etat_abeilles: isDay ? 'actif' : 'repos',
        etat_acoustique: ['calme', 'normal', 'actif'][Math.floor(Math.random() * 3)]
    };
}

// Step 1: Register user
async function registerUser() {
    console.log('\n📝 Création du compte utilisateur...');

    try {
        const response = await fetch(`${SERVER}/api/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: USER_EMAIL,
                mot_de_passe: USER_PASSWORD,
                nom: 'Demo',
                prenom: 'User',
                organisation_nom: ORG_NAME,
                organisation_type: 'recherche',
                organisation_adresse: 'Campus Jussieu, 4 Place Jussieu, 75005 Paris'
            })
        });

        const data = await response.json();

        if (response.ok) {
            TOKEN = data.token;
            console.log('✓ Compte créé avec succès!');
            console.log(`  Email: ${USER_EMAIL}`);
            console.log(`  Password: ${USER_PASSWORD}`);
            return true;
        } else if (data.error && data.error.includes('déjà utilisé')) {
            console.log('ℹ Compte existe déjà, connexion...');
            return await loginUser();
        } else {
            console.log('✗ Erreur:', data.error);
            return false;
        }
    } catch (error) {
        console.log('✗ Erreur de connexion:', error.message);
        return false;
    }
}

// Login if user exists
async function loginUser() {
    try {
        const response = await fetch(`${SERVER}/api/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: USER_EMAIL,
                mot_de_passe: USER_PASSWORD
            })
        });

        const data = await response.json();

        if (response.ok) {
            TOKEN = data.token;
            console.log('✓ Connexion réussie!');
            return true;
        } else {
            console.log('✗ Erreur de connexion:', data.error);
            return false;
        }
    } catch (error) {
        console.log('✗ Erreur:', error.message);
        return false;
    }
}

// Step 2: Generate API Key
async function generateApiKey() {
    console.log('\n🔑 Génération de la clé API...');

    try {
        const response = await fetch(`${SERVER}/api/iot/generate-key`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${TOKEN}`
            },
            body: JSON.stringify({ nom: 'Demo Setup Script' })
        });

        const data = await response.json();

        if (response.ok) {
            API_KEY = data.api_key;
            console.log('✓ Clé API générée!');
            console.log(`  ${API_KEY.substring(0, 20)}...`);
            return true;
        } else {
            console.log('✗ Erreur:', data.error);
            return false;
        }
    } catch (error) {
        console.log('✗ Erreur:', error.message);
        return false;
    }
}

// Step 3: Register ruches
async function registerRuches() {
    console.log('\n🐝 Enregistrement des ruches...');

    for (const ruche of RUCHES) {
        try {
            const response = await fetch(`${SERVER}/api/iot/register-ruche`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': API_KEY
                },
                body: JSON.stringify(ruche)
            });

            const data = await response.json();

            if (response.ok) {
                rucheIds.push(data.ruche_id);
                console.log(`✓ ${ruche.nom}`);
                console.log(`  ID: ${data.ruche_id} | ${ruche.localisation}`);
            } else {
                console.log(`✗ Erreur pour ${ruche.nom}:`, data.error);
            }
        } catch (error) {
            console.log(`✗ Erreur pour ${ruche.nom}:`, error.message);
        }
    }

    console.log(`\n✓ ${rucheIds.length} ruches enregistrées!`);
    return rucheIds.length > 0;
}

// Step 4: Send initial data for each ruche
async function sendInitialData() {
    console.log('\n📊 Envoi des données initiales...');

    for (const rucheId of rucheIds) {
        const sensorData = generateSensorData();
        sensorData.ruche_id = rucheId;

        try {
            const response = await fetch(`${SERVER}/api/iot/data`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': API_KEY
                },
                body: JSON.stringify(sensorData)
            });

            if (response.ok) {
                console.log(`✓ Ruche ${rucheId}: ${sensorData.nombre_frelons} frelons, ${sensorData.temperature}°C`);
            }
        } catch (error) {
            console.log(`✗ Erreur ruche ${rucheId}:`, error.message);
        }
    }
}

// Step 5: Generate historical data (last 24 hours)
async function generateHistoricalData() {
    console.log('\n📅 Génération de données historiques (24h)...');

    const hoursBack = 24;
    let totalSent = 0;

    for (let h = hoursBack; h > 0; h--) {
        for (const rucheId of rucheIds) {
            const timestamp = new Date(Date.now() - h * 60 * 60 * 1000);
            const sensorData = generateSensorData();
            sensorData.ruche_id = rucheId;

            try {
                const response = await fetch(`${SERVER}/api/iot/data`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-API-Key': API_KEY
                    },
                    body: JSON.stringify(sensorData)
                });

                if (response.ok) {
                    totalSent++;
                }
            } catch (error) {
                // Silent fail for historical data
            }
        }

        if (h % 4 === 0) {
            process.stdout.write(`  ${hoursBack - h}h/${hoursBack}h envoyées...\r`);
        }
    }

    console.log(`\n✓ ${totalSent} points de données historiques générés!`);
}

// Step 6: Continuous data streaming
async function startDataStreaming() {
    console.log('\n🔄 Démarrage de l\'envoi continu de données...');
    console.log('   (Ctrl+C pour arrêter)\n');

    setInterval(async () => {
        const timestamp = new Date().toLocaleTimeString('fr-FR');

        for (const rucheId of rucheIds) {
            const sensorData = generateSensorData();
            sensorData.ruche_id = rucheId;

            try {
                const response = await fetch(`${SERVER}/api/iot/data`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-API-Key': API_KEY
                    },
                    body: JSON.stringify(sensorData)
                });

                if (response.ok) {
                    console.log(`[${timestamp}] Ruche ${rucheId}: ${sensorData.nombre_frelons} frelons | ${sensorData.temperature}°C | ${sensorData.humidite}%`);
                }
            } catch (error) {
                console.log(`[${timestamp}] ✗ Erreur ruche ${rucheId}`);
            }
        }
    }, 10000); // Every 10 seconds
}

// Main execution
async function main() {
    console.log('═══════════════════════════════════════════════');
    console.log('   BeeGuardAI - Configuration Démo Automatique');
    console.log('═══════════════════════════════════════════════');

    // Step 1: Create/login user
    const userOk = await registerUser();
    if (!userOk) {
        console.log('\n❌ Impossible de créer/connecter l\'utilisateur. Arrêt.');
        process.exit(1);
    }

    // Step 2: Generate API key
    const keyOk = await generateApiKey();
    if (!keyOk) {
        console.log('\n❌ Impossible de générer la clé API. Arrêt.');
        process.exit(1);
    }

    // Step 3: Register ruches
    const ruchesOk = await registerRuches();
    if (!ruchesOk) {
        console.log('\n❌ Impossible d\'enregistrer les ruches. Arrêt.');
        process.exit(1);
    }

    // Step 4: Send initial data
    await sendInitialData();

    // Step 5: Generate historical data
    await generateHistoricalData();

    // Summary
    console.log('\n═══════════════════════════════════════════════');
    console.log('✅ CONFIGURATION TERMINÉE!');
    console.log('═══════════════════════════════════════════════');
    console.log('\n📱 Accédez au dashboard:');
    console.log(`   ${SERVER}/login.html`);
    console.log('\n🔐 Identifiants:');
    console.log(`   Email: ${USER_EMAIL}`);
    console.log(`   Password: ${USER_PASSWORD}`);
    console.log(`\n🐝 Ruches créées: ${rucheIds.length}`);
    console.log('═══════════════════════════════════════════════\n');

    // Step 6: Start continuous streaming
    await startDataStreaming();
}

// Run
main().catch(console.error);
