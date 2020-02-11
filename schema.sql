CREATE TABLE IF NOT EXISTS monitors (
  name TEXT,
  key TEXT,
  user TEXT,
  email TEXT,
  lastPing INT,
  up24h INT,
  down24h INT,
  up7d INT,
  down7d INT,
  up30d INT,
  down30d INT,
  state BOOLEAN,
  FOREIGN KEY(user) REFERENCES users(name)
);

CREATE TABLE IF NOT EXISTS users (
  name TEXT PRIMARY KEY,
  password TEXT
);

CREATE TABLE IF NOT EXISTS sessions (
  id TEXT,
  name TEXT,
  FOREIGN KEY(name) REFERENCES users(name)
);
