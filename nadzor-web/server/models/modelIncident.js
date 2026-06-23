const db = require('../configs/database');

module.exports = {
  /**
   * Создание нового инцидента
   */
  async create(deviceId, eventTypeId, title, description, status = 'open') {
    const result = await db.query(
      `INSERT INTO incidents (title, event_type_id, status, description, opened_at) 
       VALUES ($1, $2, $3, $4, NOW()) 
       RETURNING *`,
      [title, eventTypeId, status, description]
    );
    return result.rows[0];
  },

  /**
   * Получение всех активных инцидентов (status = 'open')
   */
  async getActiveIncidents() {
    const result = await db.query(
      `SELECT 
        i.id,
        i.title,
        i.status,
        i.description,
        i.opened_at,
        i.closed_at,
        et.code as event_code,
        et.name as event_name,
        et.severity
       FROM incidents i
       JOIN event_types et ON i.event_type_id = et.id
       WHERE i.status = 'open'
       ORDER BY i.opened_at DESC`
    );
    return result.rows;
  },

  /**
   * Получение инцидента по ID
   */
  async findById(id) {
    const result = await db.query(
      `SELECT 
        i.*,
        et.code as event_code,
        et.name as event_name,
        et.severity
       FROM incidents i
       JOIN event_types et ON i.event_type_id = et.id
       WHERE i.id = $1`,
      [id]
    );
    return result.rows[0] || null;
  },

  /**
   * Обновление статуса инцидента (подтвердить/опровергнуть)
   */
  async updateStatus(id, status, description = null) {
    const result = await db.query(
      `UPDATE incidents 
       SET status = $1, closed_at = NOW(), description = COALESCE($2, description)
       WHERE id = $3
       RETURNING *`,
      [status, description, id]
    );
    return result.rows[0];
  }
};