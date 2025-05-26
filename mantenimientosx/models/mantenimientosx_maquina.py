# -*- coding: utf-8 -*-

from odoo import models, fields, api

class MantenimientosXMaquina(models.Model):
    _name = 'mantenimientosx.maquina'
    _description = 'Máquinas para mantenimiento'
    _order = 'categoria_id, name'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Nombre', required=True, tracking=True)
    categoria_id = fields.Many2one('mantenimientosx.categoria', string='Categoría', required=True, tracking=True)
    horometro_id = fields.Many2one('mantenimientosx.horometro', string='Horómetro', required=True, tracking=True)
    
    # Cambiamos de Float a Integer y añadimos readonly=True
    horas_totales = fields.Integer(string='Horas totales', readonly=True)
    horas_promedio = fields.Integer(string='Horas promedio (90 últimos días)', readonly=True)
    
    active = fields.Boolean(default=True)
    
    # Nuevos campos según la imagen
    marca = fields.Char(string='Marca', tracking=True)
    modelo = fields.Char(string='Modelo', tracking=True)
    serie = fields.Char(string='Serie', tracking=True)
    
    # Relación con actividades de mantenimiento
    actividad_ids = fields.One2many('mantenimientosx.actividad.maquina', 'maquina_id', string='Actividades de mantenimiento')
    
    @api.onchange('horometro_id')
    def _onchange_horometro_id(self):
        """
        Al cambiar el horómetro, actualiza las horas totales y promedio
        """
        if self.horometro_id:
            # Obtenemos los valores del horómetro
            horas_totales = self.horometro_id.horas_totales if hasattr(self.horometro_id, 'horas_totales') else 0
            horas_promedio = self.horometro_id.horas_promedio if hasattr(self.horometro_id, 'horas_promedio') else 0
            
            # Convertimos a enteros si son float
            self.horas_totales = int(horas_totales)
            self.horas_promedio = int(horas_promedio)
    
    @api.model
    def create(self, vals):
        """
        Sobrescribimos el método create para asegurar que se guarden los valores de horas
        """
        # Si tenemos el horómetro pero no las horas, las obtenemos
        if vals.get('horometro_id') and ('horas_totales' not in vals or 'horas_promedio' not in vals):
            horometro = self.env['mantenimientosx.horometro'].browse(vals['horometro_id'])
            if horometro:
                if 'horas_totales' not in vals:
                    vals['horas_totales'] = int(horometro.horas_totales) if hasattr(horometro, 'horas_totales') else 0
                if 'horas_promedio' not in vals:
                    vals['horas_promedio'] = int(horometro.horas_promedio) if hasattr(horometro, 'horas_promedio') else 0
        
        return super(MantenimientosXMaquina, self).create(vals)
    
    def write(self, vals):
        """
        Sobrescribimos el método write para asegurar que se mantengan los valores de horas
        """
        for record in self:
            # Si se cambia el horómetro, actualizamos las horas
            if vals.get('horometro_id'):
                horometro = self.env['mantenimientosx.horometro'].browse(vals['horometro_id'])
                if horometro:
                    vals['horas_totales'] = int(horometro.horas_totales) if hasattr(horometro, 'horas_totales') else 0
                    vals['horas_promedio'] = int(horometro.horas_promedio) if hasattr(horometro, 'horas_promedio') else 0
            # Si no se cambia el horómetro y no se especifican las horas, mantenemos los valores actuales
            else:
                # Solo si no se están enviando explícitamente estos valores
                if 'horas_totales' not in vals:
                    vals['horas_totales'] = record.horas_totales
                if 'horas_promedio' not in vals:
                    vals['horas_promedio'] = record.horas_promedio
        
        return super(MantenimientosXMaquina, self).write(vals)
