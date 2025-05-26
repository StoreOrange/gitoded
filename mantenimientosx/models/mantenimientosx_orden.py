from odoo import api, fields, models, _

class MantenimientosXOrden(models.Model):
    _name = 'mantenimientosx.orden'
    _description = 'Orden de Mantenimiento'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char('N?mero de Orden', required=True, copy=False, readonly=True, default=lambda self: _('Nueva'))
    descripcion = fields.Text('Descripci?n')
    fecha_creacion = fields.Date('Fecha de Creaci?n', default=fields.Date.today)
    fecha_programada = fields.Date('Fecha Programada')
    state = fields.Selection([
        ('borrador', 'Borrador'),
        ('programada', 'Programada'),
        ('en_proceso', 'En Proceso'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada')
    ], string='Estado', default='borrador', tracking=True)
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('Nueva')) == _('Nueva'):
            vals['name'] = self.env['ir.sequence'].next_by_code('mantenimientosx.orden') or _('Nueva')
        return super(MantenimientosXOrden, self).create(vals)
    
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
