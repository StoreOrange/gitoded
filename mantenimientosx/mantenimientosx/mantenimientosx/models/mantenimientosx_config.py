from odoo import api, fields, models

class MantenimientosXCategoria(models.Model):
    _name = 'mantenimientosx.categoria'
    _description = 'Categorías de Equipo'
    
    
    name = fields.Char('Nombre', required=True)
    descripcion = fields.Text('Descripción')
    active = fields.Boolean('Activo', default=True)
    color = fields.Integer('Color')
    
    equipo_ids = fields.One2many('mantenimientosx.equipo', 'categoria_id', string='Equipos')
    equipo_count = fields.Integer(string='Número de Equipos', compute='_compute_equipo_count')
    
    @api.depends('equipo_ids')
    def _compute_equipo_count(self):
        for categoria in self:
            categoria.equipo_count = len(categoria.equipo_ids)
    
    def action_view_equipos(self):
        self.ensure_one()
        action = self.env.ref('mantenimientosx.action_mantenimientosx_equipos').read()[0]
        action['domain'] = [('categoria_id', '=', self.id)]
        action['context'] = {'default_categoria_id': self.id}
        return action

class MantenimientosXActividad(models.Model):
    _name = 'mantenimientosx.actividad'
    _description = 'Actividad de Mantenimiento'
    _order = 'sequence, id'
    
    name = fields.Char('Nombre', required=True)
    descripcion = fields.Text('Descripción')
    instrucciones = fields.Text('Instrucciones')
    sequence = fields.Integer('Secuencia', default=10)
    duracion_estimada = fields.Float('Duración Estimada', help='Duración en horas')
    requiere_herramientas = fields.Boolean('Requiere Herramientas')
    requiere_materiales = fields.Boolean('Requiere Materiales')
    active = fields.Boolean('Activo', default=True)

class MantenimientosXHorometro(models.Model):
    _name = 'mantenimientosx.horometro'
    _description = 'Registro de Horómetro'
    _order = 'fecha desc, id desc'
    
    name = fields.Char('Nombre', compute='_compute_name', store=True)
    equipo_id = fields.Many2one('mantenimientosx.equipo', string='Equipo', required=True)
    fecha = fields.Date('Fecha', default=fields.Date.today, required=True)
    lectura = fields.Float('Lectura', required=True)
    lectura_anterior = fields.Float('Lectura Anterior', compute='_compute_lectura_anterior', store=True)
    diferencia = fields.Float('Diferencia', compute='_compute_diferencia', store=True)
    notas = fields.Text('Notas')
    
    @api.depends('equipo_id', 'fecha')
    def _compute_name(self):
        for registro in self:
            if registro.equipo_id and registro.fecha:
                registro.name = f"{registro.equipo_id.name} - {registro.fecha}"
            else:
                registro.name = "Nuevo Registro"
    
    @api.depends('equipo_id', 'fecha')
    def _compute_lectura_anterior(self):
        for registro in self:
            anterior = self.search([
                ('equipo_id', '=', registro.equipo_id.id),
                ('fecha', '<', registro.fecha),
                ('id', '!=', registro.id)
            ], order='fecha desc, id desc', limit=1)
            
            registro.lectura_anterior = anterior.lectura if anterior else 0.0
    
    @api.depends('lectura', 'lectura_anterior')
    def _compute_diferencia(self):
        for registro in self:
            registro.diferencia = registro.lectura - registro.lectura_anterior