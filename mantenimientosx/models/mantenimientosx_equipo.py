from odoo import api, fields, models

class MantenimientosXEquipo(models.Model):
    _name = 'mantenimientosx.equipo'
    _description = 'Equipo de Mantenimiento'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char('Nombre', required=True)
    codigo = fields.Char('Código')
    descripcion = fields.Text('Descripción')
    fecha_adquisicion = fields.Date('Fecha de Adquisición')
    active = fields.Boolean('Activo', default=True)
    categoria_id = fields.Many2one('mantenimientosx.categoria', string='Categoría')
    
    solicitud_ids = fields.One2many('mantenimientosx.solicitud', 'equipo_id', string='Solicitudes')
    solicitud_count = fields.Integer(string='Número de Solicitudes', compute='_compute_solicitud_count')
    
    @api.depends('solicitud_ids')
    def _compute_solicitud_count(self):
        for equipo in self:
            equipo.solicitud_count = len(equipo.solicitud_ids)
    
    def action_view_solicitudes(self):
        self.ensure_one()
        action = self.env.ref('mantenimientosx.action_mantenimientosx_historico').read()[0]
        action['domain'] = [('equipo_id', '=', self.id)]
        action['context'] = {'default_equipo_id': self.id}
        return action