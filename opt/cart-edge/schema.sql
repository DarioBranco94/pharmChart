-- Reparti
CREATE TABLE ward (
    ward_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT
);

-- Carrelli
CREATE TABLE cart (
    cart_id INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT UNIQUE NOT NULL,
    model TEXT,
    serial_no TEXT
);

-- Cassetti
CREATE TABLE drawer (
    drawer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    cart_id INTEGER NOT NULL REFERENCES cart(cart_id),
    label TEXT,
    state TEXT CHECK (state IN ('open','closed')) DEFAULT 'closed'
);

-- Scomparti (mappati fisicamente come [cass][riga][colonna])
CREATE TABLE compartment (
    compartment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    drawer_id INTEGER NOT NULL REFERENCES drawer(drawer_id),
    row_index INTEGER NOT NULL,
    col_index INTEGER NOT NULL,
    physical_code TEXT UNIQUE,
    label TEXT
);

-- Operatori
CREATE TABLE staff (
    operator_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Anagrafica farmaci
CREATE TABLE drug_master (
    drug_code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    form TEXT,
    strength TEXT,
    manufacturer TEXT,
    last_updated TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Lotti farmaci
CREATE TABLE batch (
    batch_id INTEGER PRIMARY KEY AUTOINCREMENT,
    drug_code TEXT NOT NULL REFERENCES drug_master(drug_code),
    batch_number TEXT NOT NULL,
    mfg_date TEXT,
    exp_date TEXT NOT NULL,
    UNIQUE(drug_code, batch_number)
);

-- Inventario (per scomparto e lotto)
CREATE TABLE inventory (
    compartment_id INTEGER NOT NULL REFERENCES compartment(compartment_id),
    drug_code TEXT NOT NULL REFERENCES drug_master(drug_code),
    batch_id INTEGER NOT NULL REFERENCES batch(batch_id),
    qty_on_hand REAL NOT NULL,
    PRIMARY KEY (compartment_id, drug_code, batch_id)
);

-- Movimenti
CREATE TABLE movement (
    movement_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    operator_id INTEGER NOT NULL REFERENCES staff(operator_id),
    movement_type TEXT CHECK (movement_type IN (
        'carico','scarico','prelievo','somministrazione','scarto','reso'
    )),
    compartment_id INTEGER REFERENCES compartment(compartment_id),
    drug_code TEXT REFERENCES drug_master(drug_code),
    batch_id INTEGER REFERENCES batch(batch_id),
    qty REAL NOT NULL
);

-- Outbox MQTT per sincronizzazione
CREATE TABLE mqtt_outbox (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT NOT NULL,
    payload TEXT NOT NULL,
    sent BOOLEAN DEFAULT 0,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);
