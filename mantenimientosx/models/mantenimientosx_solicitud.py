from odoo import api, fields, models

class MantenimientosXSolicitud(models.Model):
    _name = 'mantenimientosx.solicitud'
    _description = 'Solicitud de Mantenimiento'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char('Nombre', required=True)
    descripcion = fields.Text('Descripción')
    fecha_solicitud = fields.Date('Fecha de Solicitud', default=fields.Date.today)
    fecha_programada = fields.Date('Fecha Programada')
    state = fields.Selection([
        ('borrador', 'Borrador'),
        ('enviada', 'Enviada'),
        ('programada', 'Programada'),
        ('en_proceso', 'En Proceso'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada')
    ], string='Estado', default='borrador', tracking=True)
    
    equipo_id = fields.Many2one('mantenimientosx.equipo', string='Equipo')
    
    # Métodos de acción
    def action_enviar(self):
        self.write({'state': 'enviada'})
    
    def action_programar(self):
        self.write({'state': 'programada'})
    
    def action_iniciar(self):
        self.write({'state': 'en_proceso'})
    
    def action_completar(self):
        self.write({'state': 'completada'})
    
    def action_cancelar(self):
        self.write({'state': 'cancelada'})
    
    def action_borrador(self):
        self.write({'state': 'borrador'})