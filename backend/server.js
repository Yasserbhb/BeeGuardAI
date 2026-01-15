const express = require('express');
const cors = require('cors');
const cookieParser = require('cookie-parser');
const path = require('path');
const { initDatabase, getDb, saveDatabase } = require('./database');
const { hashPassword, createSession, verifySession, requireAuth, requireRole, logout } = require('./auth');

const app = express();
const PORT = 3000;

app.use(cors({ credentials: true, origin: 'http://localhost:3000' }));
app.use(express.json());
app.use(cookieParser());
app.use(express.static(path.join(__dirname, '../frontend/public')));

// ==================== AUTHENTICATION ENDPOINTS ====================

// Register new user
app.post('/api/auth/register', async (req, res) => {
  try {
    const db = getDb();
    const { email, nom, prenom, mot_de_passe, organisation_nom, organisation_type } = req.body;

    // Check if user exists
    const existingUser = db.exec('SELECT id FROM utilisateurs WHERE email = ?', [email]);
    if (existingUser[0]?.values.length > 0) {
      return res.status(400).json({ error: 'Email déjà utilisé' });
    }

    // Create organization if new
    let orgId;
    const existingOrg = db.exec('SELECT id FROM organisations WHERE nom = ?', [organisation_nom]);

    if (existingOrg[0]?.values.length > 0) {
      orgId = existingOrg[0].values[0][0];
    } else {
      db.run('INSERT INTO organisations (nom, type) VALUES (?, ?)', [organisation_nom, organisation_type || 'apiculteur']);
      const result = db.exec('SELECT last_insert_rowid() as id');
      orgId = result[0].values[0][0];
    }

    // Hash password and create user
    const hashedPassword = hashPassword(mot_de_passe);
    db.run(`
      INSERT INTO utilisateurs (email, nom, prenom, mot_de_passe, role, organisation_id)
      VALUES (?, ?, ?, ?, ?, ?)
    `, [email, nom, prenom, hashedPassword, 'gestionnaire', orgId]);

    const userResult = db.exec('SELECT last_insert_rowid() as id');
    const userId = userResult[0].values[0][0];

    saveDatabase();

    // Create session
    const token = createSession(userId, email, 'gestionnaire', orgId);

    res.cookie('token', token, { httpOnly: true, maxAge: 24 * 60 * 60 * 1000 });
    res.json({
      success: true,
      token,
      user: { id: userId, email, nom, prenom, role: 'gestionnaire', organisation_id: orgId }
    });
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

// Login
app.post('/api/auth/login', (req, res) => {
  try {
    const db = getDb();
    const { email, mot_de_passe } = req.body;

    const hashedPassword = hashPassword(mot_de_passe);
    const result = db.exec(`
      SELECT id, email, nom, prenom, role, organisation_id
      FROM utilisateurs
      WHERE email = ? AND mot_de_passe = ?
    `, [email, hashedPassword]);

    if (!result[0]?.values.length) {
      return res.status(401).json({ error: 'Email ou mot de passe incorrect' });
    }

    const columns = result[0].columns;
    const row = result[0].values[0];
    const user = {};
    columns.forEach((col, i) => user[col] = row[i]);

    // Create session
    const token = createSession(user.id, user.email, user.role, user.organisation_id);

    console.log(`🔐 [POST /api/auth/login] User "${user.prenom} ${user.nom}" logged in (${user.role})`);

    res.cookie('token', token, { httpOnly: true, maxAge: 24 * 60 * 60 * 1000 });
    res.json({
      success: true,
      token,
      user
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Logout
app.post('/api/auth/logout', (req, res) => {
  const token = req.cookies?.token;
  if (token) {
    logout(token);
  }
  res.clearCookie('token');
  res.json({ success: true });
});

// Get current user
app.get('/api/auth/me', requireAuth, (req, res) => {
  try {
    const db = getDb();
    const result = db.exec(`
      SELECT u.id, u.email, u.nom, u.prenom, u.role, u.organisation_id, o.nom as organisation_nom
      FROM utilisateurs u
      LEFT JOIN organisations o ON u.organisation_id = o.id
      WHERE u.id = ?
    `, [req.user.userId]);

    if (!result[0]) {
      return res.status(404).json({ error: 'Utilisateur non trouvé' });
    }

    const columns = result[0].columns;
    const row = result[0].values[0];
    const user = {};
    columns.forEach((col, i) => user[col] = row[i]);

    res.json(user);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ==================== IOT DEVICE MANAGEMENT ====================

// Generate API key for IoT devices (protected - only gestionnaire/admin)
app.post('/api/iot/generate-key', requireAuth, requireRole('admin', 'gestionnaire'), (req, res) => {
  try {
    const db = getDb();
    const { nom } = req.body;
    const orgId = req.user.orgId;

    // Generate unique API key
    const crypto = require('crypto');
    const apiKey = 'bga_' + crypto.randomBytes(32).toString('hex');

    db.run(`
      INSERT INTO api_keys (key, organisation_id, nom)
      VALUES (?, ?, ?)
    `, [apiKey, orgId, nom || 'Device IoT']);

    saveDatabase();

    res.json({
      success: true,
      api_key: apiKey,
      message: 'Clé API créée avec succès. Conservez-la en sécurité!'
    });
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

// List API keys (protected)
app.get('/api/iot/keys', requireAuth, (req, res) => {
  try {
    const db = getDb();
    const orgId = req.user.orgId;

    const result = db.exec(`
      SELECT id, key, nom, actif, date_creation, derniere_utilisation
      FROM api_keys
      WHERE organisation_id = ?
      ORDER BY date_creation DESC
    `, [orgId]);

    if (!result[0]) return res.json([]);

    const columns = result[0].columns;
    const keys = result[0].values.map(row => {
      const obj = {};
      columns.forEach((col, i) => obj[col] = row[i]);
      // Mask the key for security (show first 10 chars)
      obj.key_masked = obj.key.substring(0, 15) + '...';
      delete obj.key;
      return obj;
    });

    res.json(keys);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Middleware to verify API key
function verifyApiKey(req, res, next) {
  const apiKey = req.headers['x-api-key'];

  if (!apiKey) {
    return res.status(401).json({ error: 'API key required' });
  }

  try {
    const db = getDb();
    const result = db.exec(`
      SELECT organisation_id, actif
      FROM api_keys
      WHERE key = ?
    `, [apiKey]);

    if (!result[0]?.values.length) {
      return res.status(401).json({ error: 'Invalid API key' });
    }

    const [orgId, actif] = result[0].values[0];

    if (!actif) {
      return res.status(401).json({ error: 'API key disabled' });
    }

    // Update last usage
    db.run(`
      UPDATE api_keys
      SET derniere_utilisation = datetime('now')
      WHERE key = ?
    `, [apiKey]);
    saveDatabase();

    req.iot = { orgId };
    next();
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

// IoT device registration - Register a new ruche (uses API key)
app.post('/api/iot/register-ruche', verifyApiKey, (req, res) => {
  try {
    const db = getDb();
    const { nom, localisation } = req.body;
    const orgId = req.iot.orgId;

    if (!nom) {
      return res.status(400).json({ error: 'nom is required' });
    }

    // Check if ruche already exists
    const existing = db.exec(`
      SELECT id FROM ruches
      WHERE nom = ? AND organisation_id = ?
    `, [nom, orgId]);

    if (existing[0]?.values.length > 0) {
      const rucheId = existing[0].values[0][0];
      return res.json({
        success: true,
        ruche_id: rucheId,
        message: 'Ruche already registered',
        existing: true
      });
    }

    // Create new ruche
    db.run(`
      INSERT INTO ruches (nom, localisation, organisation_id)
      VALUES (?, ?, ?)
    `, [nom, localisation || 'Non spécifié', orgId]);

    const result = db.exec('SELECT last_insert_rowid() as id');
    const rucheId = result[0].values[0][0];

    saveDatabase();

    res.json({
      success: true,
      ruche_id: rucheId,
      message: 'Ruche registered successfully',
      existing: false
    });
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

// IoT device sends data (uses API key)
app.post('/api/iot/data', verifyApiKey, (req, res) => {
  try {
    const db = getDb();
    const {
      ruche_nom,
      ruche_id,
      nombre_frelons,
      nombre_abeilles_entrees,
      nombre_abeilles_sorties,
      temperature,
      humidite,
      etat_abeilles,
      etat_acoustique
    } = req.body;

    const orgId = req.iot.orgId;

    // Find ruche by name or ID
    let actualRucheId = ruche_id;

    if (!actualRucheId && ruche_nom) {
      const result = db.exec(`
        SELECT id FROM ruches
        WHERE nom = ? AND organisation_id = ?
      `, [ruche_nom, orgId]);

      if (!result[0]?.values.length) {
        return res.status(404).json({ error: 'Ruche not found. Register it first.' });
      }

      actualRucheId = result[0].values[0][0];
    }

    if (!actualRucheId) {
      return res.status(400).json({ error: 'ruche_id or ruche_nom required' });
    }

    // Verify ruche belongs to organization
    const verify = db.exec(`
      SELECT id FROM ruches
      WHERE id = ? AND organisation_id = ?
    `, [actualRucheId, orgId]);

    if (!verify[0]?.values.length) {
      return res.status(403).json({ error: 'Ruche does not belong to your organization' });
    }

    // Insert data
    db.run(`
      INSERT INTO donnees_capteurs (
        ruche_id, nombre_frelons, nombre_abeilles_entrees, nombre_abeilles_sorties,
        temperature, humidite, etat_abeilles, etat_acoustique
      )
      VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    `, [
      actualRucheId,
      nombre_frelons || 0,
      nombre_abeilles_entrees || 0,
      nombre_abeilles_sorties || 0,
      temperature,
      humidite,
      etat_abeilles,
      etat_acoustique
    ]);

    const result = db.exec('SELECT last_insert_rowid() as id');
    const dataId = result[0].values[0][0];

    saveDatabase();

    res.json({
      success: true,
      data_id: dataId,
      ruche_id: actualRucheId,
      message: 'Data received successfully'
    });
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

// ==================== ENDPOINTS RUCHES ====================

// Créer une nouvelle ruche (protected)
app.post('/api/ruches', requireAuth, requireRole('admin', 'gestionnaire'), (req, res) => {
  try {
    const db = getDb();
    const { nom, localisation } = req.body;
    const orgId = req.user.orgId;

    console.log(`🏠 [POST /api/ruches] Creating: "${nom}" at ${localisation}`);

    db.run('INSERT INTO ruches (nom, localisation, organisation_id) VALUES (?, ?, ?)', [nom, localisation, orgId]);
    const result = db.exec('SELECT last_insert_rowid() as id');
    const id = result[0].values[0][0];
    saveDatabase();
    res.json({ id, nom, localisation, organisation_id: orgId });
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

// Liste toutes les ruches (filtered by organization)
app.get('/api/ruches', requireAuth, (req, res) => {
  try {
    const db = getDb();
    const orgId = req.user.orgId;
    const result = db.exec('SELECT * FROM ruches WHERE organisation_id = ?', [orgId]);
    console.log(`📋 [GET /api/ruches] Fetched ${result[0] ? result[0].values.length : 0} ruches`);
    if (!result[0]) return res.json([]);

    const columns = result[0].columns;
    const ruches = result[0].values.map(row => {
      const obj = {};
      columns.forEach((col, i) => obj[col] = row[i]);
      return obj;
    });
    res.json(ruches);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Obtenir une ruche spécifique
app.get('/api/ruches/:id', requireAuth, (req, res) => {
  try {
    const db = getDb();
    const result = db.exec('SELECT * FROM ruches WHERE id = ?', [req.params.id]);
    if (!result[0]) return res.status(404).json({ error: 'Ruche non trouvée' });

    const columns = result[0].columns;
    const row = result[0].values[0];
    const ruche = {};
    columns.forEach((col, i) => ruche[col] = row[i]);
    res.json(ruche);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ==================== ENDPOINTS DONNÉES CAPTEURS ====================

// Recevoir données IoT (pour votre capteur ESP32/Arduino)
app.post('/api/donnees', (req, res) => {
  try {
    const db = getDb();
    const {
      ruche_id,
      nombre_frelons,
      nombre_abeilles_entrees,
      nombre_abeilles_sorties,
      temperature,
      humidite,
      etat_abeilles,
      etat_acoustique,
      timestamp
    } = req.body;

    console.log(`📊 [POST /api/donnees] Ruche ${ruche_id} - Frelons: ${nombre_frelons}, Temp: ${temperature}°C ${timestamp ? '(historical)' : ''}`);

    // If timestamp is provided, use it; otherwise use CURRENT_TIMESTAMP
    if (timestamp) {
      db.run(`
        INSERT INTO donnees_capteurs (
          ruche_id, nombre_frelons, nombre_abeilles_entrees, nombre_abeilles_sorties,
          temperature, humidite, etat_abeilles, etat_acoustique, timestamp
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
      `, [
        ruche_id,
        nombre_frelons || 0,
        nombre_abeilles_entrees || 0,
        nombre_abeilles_sorties || 0,
        temperature,
        humidite,
        etat_abeilles,
        etat_acoustique,
        timestamp
      ]);
    } else {
      db.run(`
        INSERT INTO donnees_capteurs (
          ruche_id, nombre_frelons, nombre_abeilles_entrees, nombre_abeilles_sorties,
          temperature, humidite, etat_abeilles, etat_acoustique
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
      `, [
        ruche_id,
        nombre_frelons || 0,
        nombre_abeilles_entrees || 0,
        nombre_abeilles_sorties || 0,
        temperature,
        humidite,
        etat_abeilles,
        etat_acoustique
      ]);
    }

    const result = db.exec('SELECT last_insert_rowid() as id');
    const id = result[0].values[0][0];
    saveDatabase();
    res.json({ id, message: 'Données enregistrées avec succès' });
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

// Obtenir dernières données d'une ruche
app.get('/api/ruches/:id/donnees/latest', (req, res) => {
  try {
    const db = getDb();
    const result = db.exec(`
      SELECT * FROM donnees_capteurs
      WHERE ruche_id = ?
      ORDER BY timestamp DESC
      LIMIT 1
    `, [req.params.id]);

    if (!result[0]) return res.status(404).json({ error: 'Aucune donnée' });

    const columns = result[0].columns;
    const row = result[0].values[0];
    const data = {};
    columns.forEach((col, i) => data[col] = row[i]);
    res.json(data);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Obtenir historique données d'une ruche
app.get('/api/ruches/:id/donnees', (req, res) => {
  try {
    const db = getDb();
    const limit = req.query.limit || 100;
    console.log(`📊 [GET /api/ruches/${req.params.id}/donnees] Fetching ${limit} historical data points`);
    const result = db.exec(`
      SELECT * FROM donnees_capteurs
      WHERE ruche_id = ?
      ORDER BY timestamp DESC
      LIMIT ?
    `, [req.params.id, limit]);

    if (!result[0]) return res.json([]);

    const columns = result[0].columns;
    const data = result[0].values.map(row => {
      const obj = {};
      columns.forEach((col, i) => obj[col] = row[i]);
      return obj;
    });
    console.log(`   ✓ Returned ${data.length} data points for chart`);
    res.json(data);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Obtenir toutes les dernières données (dashboard) - filtered by organization
app.get('/api/donnees/latest', requireAuth, (req, res) => {
  try {
    const db = getDb();
    const orgId = req.user.orgId;
    const result = db.exec(`
      SELECT
        r.id as ruche_id,
        r.nom,
        r.localisation,
        d.nombre_frelons,
        d.nombre_abeilles_entrees,
        d.nombre_abeilles_sorties,
        d.temperature,
        d.humidite,
        d.etat_abeilles,
        d.etat_acoustique,
        d.timestamp
      FROM ruches r
      LEFT JOIN donnees_capteurs d ON r.id = d.ruche_id
      WHERE r.organisation_id = ? AND (d.id IN (
        SELECT MAX(id) FROM donnees_capteurs GROUP BY ruche_id
      ) OR d.id IS NULL)
    `, [orgId]);

    if (!result[0]) return res.json([]);

    const columns = result[0].columns;
    const data = result[0].values.map(row => {
      const obj = {};
      columns.forEach((col, i) => obj[col] = row[i]);
      return obj;
    });
    console.log(`📈 [GET /api/donnees/latest] Returned ${data.length} ruches with latest data`);
    res.json(data);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ==================== SERVER ====================

initDatabase().then(() => {
  app.listen(PORT, () => {
    console.log(`\nServeur BeeGuardAI démarré sur http://localhost:${PORT}`);
    console.log(`\nDashboard: http://localhost:${PORT}`);
    console.log(`\nEndpoints API:`);
    console.log(`  POST   /api/ruches - Créer une ruche`);
    console.log(`  GET    /api/ruches - Liste des ruches`);
    console.log(`  POST   /api/donnees - Envoyer données capteur`);
    console.log(`  GET    /api/donnees/latest - Dernières données toutes ruches`);
    console.log(`  GET    /api/ruches/:id/donnees/latest - Dernière donnée d'une ruche\n`);
  });
}).catch(err => {
  console.error('Erreur initialisation database:', err);
  process.exit(1);
});
