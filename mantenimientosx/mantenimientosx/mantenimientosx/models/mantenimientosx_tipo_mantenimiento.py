from odoo import api, fields, models

class MantenimientosXTipoMantenimiento(models.Model):
    _name = 'mantenimientosx.tipo.mantenimiento'
    _description = 'Tipo de Mantenimiento'
    
    name = fields.Char('Nombre', required=True)
    descripcion = fields.Text('Descripción')
    active = fields.Boolean(default=True)