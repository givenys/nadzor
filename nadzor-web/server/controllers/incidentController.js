const modelIncident = require('../models/modelIncident');

/**
 * Создание инцидента (вызывается Python-скриптом)
 */
exports.createIncident = async (req, res) => {
  try {
    const { device_id, event_type_id, status, title, description } = req.body;

    if (!device_id || !event_type_id || !title) {
      return res.status(400).json({ error: 'device_id, event_type_id and title are required' });
    }

    const incident = await modelIncident.create(
      device_id,
      event_type_id,
      title,
      description,
      status || 'open'
    );

    // Broadcast всем зрителям инцидентов
    if (global.incidentViewers) {
      const message = JSON.stringify({
        type: 'new_incident',
        incident: {
          id: incident.id,
          title: incident.title,
          status: incident.status,
          description: incident.description,
          opened_at: incident.opened_at,
          device_id: device_id
        }
      });

      global.incidentViewers.forEach(client => {
        if (client.readyState === 1) { // WebSocket.OPEN
          client.send(message);
        }
      });
    }

    res.status(201).json({ 
      message: 'Incident created',
      incident 
    });
  } catch (err) {
    console.error('Create incident error:', err);
    res.status(500).json({ error: 'Failed to create incident' });
  }
};

/**
 * Получение всех активных инцидентов
 */
exports.getActiveIncidents = async (req, res) => {
  try {
    const incidents = await modelIncident.getActiveIncidents();
    res.json(incidents);
  } catch (err) {
    console.error('Get active incidents error:', err);
    res.status(500).json({ error: 'Failed to load incidents' });
  }
};

/**
 * Ответ оператора на инцидент (подтвердить/опровергнуть)
 */
exports.respondToIncident = async (req, res) => {
  try {
    const { id } = req.params;
    const { action } = req.body; // 'confirm' или 'reject'

    if (!action || !['confirm', 'reject'].includes(action)) {
      return res.status(400).json({ error: 'action must be "confirm" or "reject"' });
    }

    const incident = await modelIncident.findById(id);
    if (!incident) {
      return res.status(404).json({ error: 'Incident not found' });
    }

    if (incident.status !== 'open') {
      return res.status(400).json({ error: 'Incident already closed' });
    }

    const newStatus = action === 'confirm' ? 'confirmed' : 'rejected';
    const description = action === 'confirm' ? 'confirmed' : 'rejected';

    const updatedIncident = await modelIncident.updateStatus(id, newStatus, description);

    // Broadcast всем зрителям инцидентов
    if (global.incidentViewers) {
      const message = JSON.stringify({
        type: 'incident_resolved',
        incident_id: id,
        action: action,
        status: newStatus
      });

      global.incidentViewers.forEach(client => {
        if (client.readyState === 1) {
          client.send(message);
        }
      });
    }

    res.json({ 
      message: `Incident ${action}ed`,
      incident: updatedIncident 
    });
  } catch (err) {
    console.error('Respond to incident error:', err);
    res.status(500).json({ error: 'Failed to respond to incident' });
  }
};