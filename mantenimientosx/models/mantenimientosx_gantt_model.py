from odoo import models

class MantenimientosXGanttView(models.TransientModel):  # O models.Model si quieres registros persistentes
    _name = 'mantenimientosx.gantt.view'
    _description = 'Vista integrada del cronograma Gantt'

