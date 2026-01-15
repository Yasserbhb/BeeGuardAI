const initSqlJs = require('sql.js');
const fs = require('fs');
const path = require('path');

const dbPath = path.join(__dirname, 'ruches.db');
let db;

async function initDatabase() {
  const SQL = await initSqlJs();

  let data;
  if (fs.existsSync(dbPath)) {
    data = fs.readFileSync(dbPath);
  }

  db = new SQL.Database(data || undefined);

  // Créer la table des organisations
  db.run(`
    CREATE TABLE IF NOT EXISTS organisations (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      nom TEXT NOT NULL UNIQUE,
      type TEXT CHECK(type IN ('apiculteur', 'recherche', 'collectivite')),
      adresse TEXT,
      date_creation TEXT DEFAULT (datetime('now'))
    )
  `);

  // Créer la table des utilisateurs
  db.run(`
    CREATE TABLE IF NOT EXISTS utilisateurs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      email TEXT NOT NULL UNIQUE,
      nom TEXT NOT NULL,
      prenom TEXT NOT NULL,
      mot_de_passe TEXT NOT NULL,
      role TEXT CHECK(role IN ('admin', 'gestionnaire', 'observateur')) DEFAULT 'observateur',
      organisation_id INTEGER,
      date_creation TEXT DEFAULT (datetime('now')),
      FOREIGN KEY (organisation_id) REFERENCES organisations(id)
    )
  `);

  // Créer la table des API keys pour les devices IoT
  db.run(`
    CREATE TABLE IF NOT EXISTS api_keys (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      key TEXT NOT NULL UNIQUE,
      organisation_id INTEGER NOT NULL,
      nom TEXT NOT NULL,
      actif INTEGER DEFAULT 1,
      date_creation TEXT DEFAULT (datetime('now')),
      derniere_utilisation TEXT,
      FOREIGN KEY (organisation_id) REFERENCES organisations(id)
    )
  `);

  // Créer la table des ruches
  db.run(`
    CREATE TABLE IF NOT EXISTS ruches (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      nom TEXT NOT NULL,
      localisation TEXT,
      organisation_id INTEGER NOT NULL,
      date_creation TEXT DEFAULT (datetime('now')),
      FOREIGN KEY (organisation_id) REFERENCES organisations(id),
      UNIQUE(nom, organisation_id)
    )
  `);

  // Créer la table des données de capteurs (état monitoring seulement)
  db.run(`
    CREATE TABLE IF NOT EXISTS donnees_capteurs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      ruche_id INTEGER NOT NULL,
      nombre_frelons INTEGER DEFAULT 0,
      nombre_abeilles_entrees INTEGER DEFAULT 0,
      nombre_abeilles_sorties INTEGER DEFAULT 0,
      temperature REAL,
      humidite REAL,
      etat_abeilles TEXT,
      etat_acoustique TEXT,
      timestamp TEXT DEFAULT (datetime('now')),
      FOREIGN KEY (ruche_id) REFERENCES ruches(id)
    )
  `);

  // Créer index pour les requêtes rapides
  db.run(`
    CREATE INDEX IF NOT EXISTS idx_ruche_timestamp
    ON donnees_capteurs(ruche_id, timestamp DESC)
  `);

  console.log('Database initialized');
  return db;
}

function saveDatabase() {
  if (db) {
    try {
      const data = db.export();
      if (data && data.length > 0) {
        fs.writeFileSync(dbPath, data);
      }
    } catch (error) {
      console.error('Error saving database:', error);
    }
  }
}

// Sauvegarder la base toutes les 30 secondes
setInterval(saveDatabase, 30000);

// Sauvegarder avant de quitter
process.on('exit', saveDatabase);
process.on('SIGINT', () => {
  saveDatabase();
  process.exit();
});

module.exports = { initDatabase, getDb: () => db, saveDatabase };
