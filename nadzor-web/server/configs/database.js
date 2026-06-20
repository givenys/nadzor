const { Pool } = require("pg");

// Создаем пул подключений для PostgreSQL
const pool = new Pool({
  host: process.env.DB_HOST,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME,
  port: process.env.DB_PORT,
  max: 10, // аналог connectionLimit в mysql2
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

pool.checkConnection = (callback) => {
  pool.query('SELECT 1 + 1 AS solution', (err, result) => {
    if (err) {
      console.error('DB connection error:', err.message);
      if (callback) callback(err);
      return;
    }

    console.log('DB (PostgreSQL) connected, solution:', result.rows[0].solution);
    if (callback) callback(null, result);
  });
};

module.exports = pool;