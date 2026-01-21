"""
BeeGuardAI - MySQL Database
"""

import hashlib
import pymysql
from pymysql.cursors import DictCursor
from app.config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE


def get_db():
    """Get MySQL connection"""
    return pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        cursorclass=DictCursor,
        autocommit=True
    )


def init_database():
    """Initialize database tables and default data"""
    conn = get_db()
    cursor = conn.cursor()

    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS organisations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nom VARCHAR(255) UNIQUE NOT NULL,
            adresse VARCHAR(500),
            date_creation DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS utilisateurs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            mot_de_passe VARCHAR(255) NOT NULL,
            nom VARCHAR(255),
            prenom VARCHAR(255),
            role ENUM('admin', 'gestionnaire', 'lecteur') DEFAULT 'lecteur',
            organisation_id INT,
            date_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (organisation_id) REFERENCES organisations(id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ruchers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nom VARCHAR(255) NOT NULL,
            localisation VARCHAR(500),
            organisation_id INT,
            date_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (organisation_id) REFERENCES organisations(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ruches (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nom VARCHAR(255) NOT NULL,
            ttn_device_id VARCHAR(100) UNIQUE,
            rucher_id INT,
            organisation_id INT,
            date_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (rucher_id) REFERENCES ruchers(id) ON DELETE SET NULL,
            FOREIGN KEY (organisation_id) REFERENCES organisations(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            token VARCHAR(64) PRIMARY KEY,
            user_id INT,
            email VARCHAR(255),
            role VARCHAR(50),
            organisation_id INT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES utilisateurs(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    ''')

    # Create default organization and admin
    cursor.execute("SELECT id FROM organisations WHERE nom = 'Sorbonne Université'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO organisations (nom, adresse) VALUES ('Sorbonne Université', 'Paris, France')")
        org_id = cursor.lastrowid

        password_hash = hashlib.sha256("admin123".encode()).hexdigest()
        cursor.execute('''
            INSERT INTO utilisateurs (email, mot_de_passe, nom, prenom, role, organisation_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', ('admin@sorbonne.fr', password_hash, 'Admin', 'Super', 'admin', org_id))

        # Create default ruchers (apiaries)
        cursor.execute("INSERT INTO ruchers (nom, localisation, organisation_id) VALUES ('Jardin Nord', 'Campus Jussieu - Zone Nord', %s)", (org_id,))
        rucher_nord_id = cursor.lastrowid
        cursor.execute("INSERT INTO ruchers (nom, localisation, organisation_id) VALUES ('Jardin Sud', 'Campus Jussieu - Zone Sud', %s)", (org_id,))
        rucher_sud_id = cursor.lastrowid

        # Create default ruches with TTN device IDs
        cursor.execute("INSERT INTO ruches (nom, ttn_device_id, rucher_id, organisation_id) VALUES ('Ruche Alpha', 'beehive-001', %s, %s)", (rucher_nord_id, org_id))
        cursor.execute("INSERT INTO ruches (nom, ttn_device_id, rucher_id, organisation_id) VALUES ('Ruche Beta', 'beehive-002', %s, %s)", (rucher_nord_id, org_id))
        cursor.execute("INSERT INTO ruches (nom, ttn_device_id, rucher_id, organisation_id) VALUES ('Ruche Gamma', 'beehive-003', %s, %s)", (rucher_sud_id, org_id))

    conn.close()
    print("✅ MySQL database initialized")
