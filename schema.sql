CREATE TABLE IF NOT EXISTS monitors (
  name TEXT,
  key TEXT,
  email TEXT,
  lastPing INT,
  up24h INT,
  up7d INT,
  up30d INT
);

INSERT INTO monitors VALUES ("kingman", "asdadggjasdhsadg", "mr.zacharycotton@gmail.com", 0,0,0,0);
