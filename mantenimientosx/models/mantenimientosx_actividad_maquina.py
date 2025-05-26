# -*- coding: utf-8 -*-

from odoo import models, fields, api

class MantenimientosXActividadMaquina(models.Model):
    _name = 'mantenimientosx.actividad.maquina'
    _description = 'Actividades por máquina'
    _order = 'categoria_id, horometro_id, maquina_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Añadimos herencia para trazabilidad/chatter
    
    # Cambiamos el campo actividad para que sea seleccionable desde el catálogo
    # Cambiamos la etiqueta de 'Nombre' a 'Actividad'
    actividad_id = fields.Many2one('mantenimientosx.actividad', string='Actividad', required=True, tracking=True)
    
    # Mantenemos el campo name como calculado
    name = fields.Char(string='Nombre', compute='_compute_name', store=True)
    
    categoria_id = fields.Many2one('mantenimientosx.categoria', string='Categoría', readonly=True, tracking=True)
    horometro_id = fields.Many2one('mantenimientosx.horometro', string='Horómetro', readonly=True, tracking=True)
    maquina_id = fields.Many2one('mantenimientosx.maquina', string='Máquina', required=True, tracking=True)
    
    # Mantenemos el campo actividad como texto pero lo hacemos calculado
    actividad = fields.Text(string='Actividad de mantenimiento', compute='_compute_actividad', store=True, tracking=True)
    
    dias_para_mto = fields.Integer(string='Días para mto.', default=0)
    orden_pendiente = fields.Char(string='OT pendiente', readonly=True)
    active = fields.Boolean(default=True)
    
    # Campos para mantenimiento - Cambiamos a Integer
    dias_para_planificacion = fields.Integer(string='Días para planificación', tracking=True)
    ultimo_mto = fields.Integer(string='Último mtto.', tracking=True)
    intervalo_mto = fields.Integer(string='Intervalo mtto.', tracking=True)
    proximo_mto = fields.Integer(string='Próximo mtto.', compute='_compute_proximo_mto', store=True)
    
    # Campos calculados según las fórmulas - Cambiamos a Integer
    horas_prox_mto = fields.Integer(string='Horas Próx. mtto.', compute='_compute_campos_calculados', store=True)
    dias_prox_mto = fields.Integer(string='Días Próx. mtto.', compute='_compute_campos_calculados', store=True)
    dias_sig_mto = fields.Integer(string='Días Sig. mtto.', compute='_compute_campos_calculados', store=True)
    
    @api.depends('maquina_id', 'actividad_id')
    def _compute_name(self):
        for record in self:
            if record.maquina_id and record.actividad_id:
                record.name = f"{record.maquina_id.name} - {record.actividad_id.name}"
            else:
                record.name = "Nueva actividad"
    
    @api.depends('actividad_id')
    def _compute_actividad(self):
        """
        Calcula el texto de la actividad basado en el nombre seleccionado
        """
        for record in self:
            if record.actividad_id:
                record.actividad = record.actividad_id.name
            else:
                record.actividad = False
    
    @api.depends('ultimo_mto', 'intervalo_mto')
    def _compute_proximo_mto(self):
        for record in self:
            # Siempre calculamos el próximo mtto, incluso si último mtto es cero
            if record.intervalo_mto:
                record.proximo_mto = record.ultimo_mto + record.intervalo_mto
            else:
                record.proximo_mto = record.ultimo_mto
    
    @api.depends('proximo_mto', 'intervalo_mto', 'maquina_id', 'maquina_id.horometro_id', 'maquina_id.horometro_id.horas_totales', 'maquina_id.horometro_id.horas_promedio')
    def _compute_campos_calculados(self):
        for record in self:
            # Obtener horas totales y promedio del horómetro asociado a la máquina
            horas_totales = record.maquina_id.horometro_id.horas_totales if record.maquina_id and record.maquina_id.horometro_id else 0
            horas_promedio = record.maquina_id.horometro_id.horas_promedio if record.maquina_id and record.maquina_id.horometro_id else 1  # Evitar división por cero
            
            # Calcular Horas Próx. mtto.
            record.horas_prox_mto = int(record.proximo_mto - horas_totales)
            
            # Calcular Días Próx. mtto.
            if horas_promedio:
                record.dias_prox_mto = int(record.horas_prox_mto / horas_promedio)
            else:
                record.dias_prox_mto = 0
            
            # Calcular Días Sig. mtto.
            if horas_promedio:
                record.dias_sig_mto = int((record.horas_prox_mto + record.intervalo_mto) / horas_promedio)
            else:
                record.dias_sig_mto = 0
    
    @api.onchange('maquina_id')
    def _onchange_maquina_id(self):
        """
        Al cambiar la máquina, actualiza automáticamente la categoría y el horómetro
        """
        if self.maquina_id:
            self.categoria_id = self.maquina_id.categoria_id
            self.horometro_id = self.maquina_id.horometro_id
    
    @api.model
    def create(self, vals):
        """
        Sobrescribe el método create para asegurar que se mantengan los valores
        de categoría y horómetro
        """
        # Si tenemos máquina pero no categoría o horómetro, los obtenemos de la máquina
        if vals.get('maquina_id'):
            maquina = self.env['mantenimientosx.maquina'].browse(vals['maquina_id'])
            if maquina:
                vals['categoria_id'] = maquina.categoria_id.id
                vals['horometro_id'] = maquina.horometro_id.id
        
        return super(MantenimientosXActividadMaquina, self).create(vals)

    def write(self, vals):
        """
        Sobrescribe el método write para asegurar que se mantengan los valores
        de categoría y horómetro
        """
        result = super(MantenimientosXActividadMaquina, self).write(vals)
        
        # Si se cambió la máquina, actualizamos categoría y horómetro
        if vals.get('maquina_id'):
            for record in self:
                maquina = self.env['mantenimientosx.maquina'].browse(vals['maquina_id'])
                if maquina:
                    record.write({
                        'categoria_id': maquina.categoria_id.id,
                        'horometro_id': maquina.horometro_id.id
                    })
        
        return result