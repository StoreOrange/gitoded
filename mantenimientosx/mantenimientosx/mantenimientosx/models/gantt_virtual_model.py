# models/gantt_virtual_model.py
from odoo import models, fields

class MantenimientosXGanttView(models.TransientModel):  # o models.Model si lo deseas persistente
    _name = 'mantenimientosx.gantt.view'
    _description = 'Vista integrada del cronograma Gantt'
