from odoo import api, fields, models

class MantenimientosXHorometro(models.Model):
    _name = 'mantenimientosx.horometro'
    _description = 'Horómetro de Equipos'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Añadido para soporte de mensajería
    
    name = fields.Char('Horómetro', required=True, tracking=True)
    fecha = fields.Date('Fecha inicial', default=fields.Date.today, tracking=True)  # Usamos 'fecha' en lugar de 'fecha_inicial'
    horas_iniciales = fields.Float('Horas iniciales', digits=(10, 3), tracking=True)
    horas_totales = fields.Float('Horas totales', digits=(10, 3), tracking=True)
    horas_promedio = fields.Float('Horas promedio', digits=(10, 3), tracking=True)
    lectura = fields.Float('Lectura', digits=(10, 3), tracking=True)
    lectura_anterior = fields.Float('Lectura anterior', digits=(10, 3), readonly=True)
    diferencia = fields.Float('Diferencia', digits=(10, 3), compute='_compute_diferencia', store=True)
    
    equipo_id = fields.Many2one('mantenimientosx.equipo', string='Equipo', tracking=True)
    active = fields.Boolean(default=True)
    
    @api.depends('lectura', 'lectura_anterior')
    def _compute_diferencia(self):
        for record in self:
            record.diferencia = record.lectura - record.lectura_anterior if record.lectura_anterior else record.lectura
    
    @api.model
    def create(self, vals):
        # Si se está creando un registro para un equipo existente, buscar la última lectura
        if vals.get('equipo_id'):
            ultimo_horometro = self.search([
                ('equipo_id', '=', vals['equipo_id'])
            ], order='create_date DESC', limit=1)
            
            if ultimo_horometro:
                vals['lectura_anterior'] = ultimo_horometro.lectura
        
        return super(MantenimientosXHorometro, self).create(vals)
    
    def action_save(self):
        """
        Método para guardar el registro y volver a la vista de lista
        """
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mantenimientosx.horometro',
            'view_mode': 'tree,form',
            'view_id': False,
            'target': 'current',
        }