from odoo import api, fields, models

class MantenimientosXHorometro(models.Model):
    _name = 'mantenimientosx.horometro'
    _description = 'Horómetro de Equipos'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Añadido para soporte de mensajería el famos chatter solicitado por doña Daysi.

    name = fields.Char('Horómetro', required=True, tracking=True)
    fecha = fields.Date('Fecha inicial', default=fields.Date.today, tracking=True)

    horas_iniciales = fields.Integer('Horas iniciales', tracking=True)
    horas_totales = fields.Integer('Horas totales')
    horas_promedio = fields.Integer('Horas promedio', default=8)

    lectura = fields.Float('Lectura', digits=(10, 3), tracking=True)
    lectura_anterior = fields.Float('Lectura anterior', digits=(10, 3), readonly=True)
    diferencia = fields.Float('Diferencia', digits=(10, 3), compute='_compute_diferencia', store=True)

    equipo_id = fields.Many2one('mantenimientosx.equipo', string='Equipo', tracking=True)
    active = fields.Boolean(default=True)
    
    # Relación inversa para encontrar máquinas asociadas a este horómetro
    maquina_ids = fields.One2many('mantenimientosx.maquina', 'horometro_id', string='Máquinas')
    
    # Relación inversa para encontrar actividades asociadas a máquinas con este horómetro
    actividad_maquina_ids = fields.One2many('mantenimientosx.actividad.maquina', 'horometro_id', string='Actividades de máquinas')

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

    def write(self, vals):
        """
        Sobrescribimos el método write para actualizar las máquinas asociadas
        cuando se modifican las horas totales o promedio del horómetro
        """
        result = super(MantenimientosXHorometro, self).write(vals)
        
        # Si se actualizaron las horas totales o promedio
        if 'horas_totales' in vals or 'horas_promedio' in vals:
            for record in self:
                # Actualizar todas las máquinas que usan este horómetro
                if record.maquina_ids:
                    for maquina in record.maquina_ids:
                        update_vals = {}
                        if 'horas_totales' in vals:
                            update_vals['horas_totales'] = vals['horas_totales']
                        if 'horas_promedio' in vals:
                            update_vals['horas_promedio'] = vals['horas_promedio']
                        
                        if update_vals:
                            maquina.write(update_vals)
                
                # Forzar el recálculo de los campos calculados en las actividades de maaquina
                if record.actividad_maquina_ids:
                    for actividad in record.actividad_maquina_ids:
                        actividad._compute_campos_calculados()
        
        return result

    def action_save(self):
        """
        Método para guardar el registro y volver a la vista de lista de defecto (aca nada se modifico   )
        """
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mantenimientosx.horometro',
            'view_mode': 'tree,form',
            'view_id': False,
            'target': 'current',
        }
