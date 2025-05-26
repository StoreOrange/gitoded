# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta

class MantenimientosXCronologicoMaquina(models.Model):
    _name = 'mantenimientosx.cronologico.maquina'
    _description = 'Cronológico de Máquina'
    _order = 'fecha desc, doc_id desc'
    
    fecha = fields.Date(string='Fecha', required=True)
    doc_id = fields.Char(string='Documento', required=True)
    maquina_id = fields.Many2one('mantenimientosx.maquina', string='Máquina', required=True)
    categoria_id = fields.Many2one('mantenimientosx.categoria', string='Categoría', required=True)
    horometro_id = fields.Many2one('mantenimientosx.horometro', string='Horómetro', required=True)
    actividad_id = fields.Many2one('mantenimientosx.actividad.maquina', string='Actividad ID')
    actividad = fields.Text(string='Actividad de mantenimiento')
    ultimo_mto = fields.Float(string='Último mtto.', digits=(16, 3))
    intervalo_mto = fields.Float(string='Intervalo mtto.', digits=(16, 3))
    proximo_mto = fields.Float(string='Próximo mtto.', digits=(16, 3))
    horas_prox_mto = fields.Integer(string='Horas Próx. mtto.')
    dias_prox_mto = fields.Integer(string='Días Próx. mtto.')
    dias_sig_mto = fields.Integer(string='Días Sig. mtto.')
    dias_para_planificacion = fields.Integer(string='Días para planificación')
    orden_pendiente = fields.Char(string='Orden pendiente')
    active = fields.Boolean(default=True)
    
    # Campos para la vista Gantt
    fecha_inicio = fields.Date(string='Fecha Inicio', compute='_compute_fechas_gantt', store=True)
    fecha_fin = fields.Date(string='Fecha Fin', compute='_compute_fechas_gantt', store=True)
    banda = fields.Char(string='Banda', compute='_compute_banda', store=True)
    color = fields.Integer(string='Color', compute='_compute_color', store=True)
    
    @api.depends('maquina_id', 'categoria_id')
    def _compute_banda(self):
        """Calcula la banda basada en la máquina y categoría"""
        for record in self:
            if record.maquina_id:
                # Extraer el número de la banda del nombre de la máquina si existe
                nombre_maquina = record.maquina_id.name or ''
                if 'Banda' in nombre_maquina or 'banda' in nombre_maquina:
                    record.banda = nombre_maquina
                else:
                    # Si no tiene "Banda" en el nombre, usar la categoría
                    record.banda = record.categoria_id.name if record.categoria_id else 'Sin Banda'
            else:
                record.banda = 'Sin Banda'
    
    @api.depends('actividad')
    def _compute_color(self):
        """Asigna un color basado en el tipo de actividad"""
        for record in self:
            if not record.actividad:
                record.color = 0
                continue
                
            actividad = record.actividad.lower() if record.actividad else ''
            
            if 'cambio' in actividad:
                record.color = 1  # Rojo
            elif 'lubricación' in actividad or 'lubricacion' in actividad:
                record.color = 2  # Verde
            elif 'engrase' in actividad:
                record.color = 3  # Azul
            elif 'verificar' in actividad or 'ajustar' in actividad:
                record.color = 4  # Amarillo
            elif 'inspección' in actividad or 'inspeccion' in actividad:
                record.color = 5  # Morado
            elif 'ajuste' in actividad:
                record.color = 6  # Naranja
            else:
                record.color = 0  # Gris (por defecto)
    
    @api.depends('fecha', 'dias_prox_mto')
    def _compute_fechas_gantt(self):
        """Calcula las fechas de inicio y fin para la vista Gantt"""
        for record in self:
            if record.fecha:
                record.fecha_inicio = record.fecha
                
                # Si tiene días próximos, calcular fecha fin
                if record.dias_prox_mto and record.dias_prox_mto > 0:
                    record.fecha_fin = record.fecha + timedelta(days=record.dias_prox_mto)
                else:
                    # Si no tiene días próximos, usar 1 día por defecto
                    record.fecha_fin = record.fecha + timedelta(days=1)
            else:
                record.fecha_inicio = fields.Date.today()
                record.fecha_fin = fields.Date.today() + timedelta(days=1)
