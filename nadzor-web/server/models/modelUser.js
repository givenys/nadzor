const db = require('./../configs/database.js');
const bcrypt = require('bcrypt');

module.exports = {
  async findByLogin(login) {
    const result = await db.query(
      `SELECT 
         o.id, o.login, o.password, o.role AS operator_role,
         e.full_name, e.role AS employee_role, e.face_embedding
       FROM operators o
       JOIN employees e ON e.id = o.id
       WHERE o.login = $1`,
      [login]
    );
    return result.rows[0] || null;
  },

  async create(login, full_name, password, role = 'operator') {
    const hashedPassword = await bcrypt.hash(password, 10);
    
    const client = await db.connect();
    try {
      await client.query('BEGIN');

      const empRes = await client.query(
        `INSERT INTO employees (full_name, role) 
         VALUES ($1, $2) 
         RETURNING id`,
        [full_name, role]
      );
      const employeeId = empRes.rows[0].id;

      await client.query(
        `INSERT INTO operators (id, login, password, role) 
         VALUES ($1, $2, $3, $4)`,
        [employeeId, login, hashedPassword, role]
      );

      await client.query('COMMIT');
      return { id: employeeId, login, full_name, role };
    } catch (err) {
      await client.query('ROLLBACK');
      throw err;
    } finally {
      client.release();
    }
  },

  async verifyPassword(operator, password) {
    return bcrypt.compare(password, operator.password);
  },

  async findById(id) {
    const result = await db.query(
      `SELECT 
         o.id, o.login, o.role AS operator_role,
         e.full_name, e.role AS employee_role, e.face_embedding
       FROM operators o
       JOIN employees e ON e.id = o.id
       WHERE o.id = $1`,
      [id]
    );
    return result.rows[0] || null;
  }
};