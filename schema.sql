CREATE TABLE IF NOT EXISTS users (
  name VARCHAR(50),
  password VARCHAR(50),
  PRIMARY KEY(name)
);

CREATE TABLE IF NOT EXISTS monitors (
  name VARCHAR(50),
  key VARCHAR(50),
  user_ VARCHAR(50) REFERENCES users(name),
  email VARCHAR(50),
  lastPing INT,
  up24h INT,
  down24h INT,
  up7d INT,
  down7d INT,
  up30d INT,
  down30d INT,
  state BOOLEAN
);

CREATE TABLE IF NOT EXISTS sessions (
  id VARCHAR(50),
  name VARCHAR(50) REFERENCES users(name)
);
