from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class MantenimientosXHorasTrabajadas(models.Model):
    _name = 'mantenimientosx.horas.trabajadas'
    _description = 'Horas Trabajadas'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha desc, name desc'
    
    name = fields.Char(string='Nombre', required=True, copy=False, readonly=True, tracking=True, 
                      default=lambda self: _('Nuevo'))
    next_number = fields.Char(string='Próximo número', compute='_compute_next_number')
    fecha = fields.Date(string='Fecha', required=True, tracking=True, default=lambda self: self._get_fecha_default())
    state = fields.Selection([
        ('borrador', 'Borrador'),
        ('confirmado', 'Confirmado'),
    ], string='Estado', default='borrador', tracking=True)
    detalle_ids = fields.One2many('mantenimientosx.horas.trabajadas.detalle', 'horas_trabajadas_id', 
                                 string='Lectura de horómetros')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Compañía', 
                                default=lambda self: self.env.company)
    
    @api.depends('name')
    def _compute_next_number(self):
        """Calcula el próximo número de secuencia para mostrar (sin consumirlo)"""
        for record in self:
            if record.name == _('Nuevo'):
                sequence = self.env['ir.sequence'].sudo().search([('code', '=', 'mantenimientosx.horas.trabajadas')], limit=1)
                if sequence:
                    record.next_number = sequence.get_next_char(sequence.number_next_actual)
                else:
                    record.next_number = 'HT000001'
            else:
                record.next_number = record.name
    
    @api.model
    def _get_fecha_default(self):
        """
        Obtiene la fecha para un nuevo registro según la lógica:
        1. Si hay registros previos, la fecha siguiente a la última
        2. Si no hay registros pero hay horómetros, la fecha máxima de horómetros
        3. Si no hay nada, la fecha actual
        """
        # Buscar la última lectura de horas trabajadas
        ultima_lectura = self.search([], order='fecha desc', limit=1)
        if ultima_lectura:
            return ultima_lectura.fecha + timedelta(days=1)
        
        # Si no hay lecturas previas, buscar la fecha máxima en horómetros
        ultimo_horometro = self.env['mantenimientosx.horometro'].search([], order='write_date desc', limit=1)
        if ultimo_horometro and ultimo_horometro.write_date:
            return fields.Date.context_today(self, ultimo_horometro.write_date)
        
        # Si no hay horómetros, usar la fecha actual
        return fields.Date.context_today(self)
    
    @api.model_create_multi
    def create(self, vals_list):
        """Al crear, no asignamos automáticamente la secuencia"""
        result = super(MantenimientosXHorasTrabajadas, self).create(vals_list)
        
        # Crear líneas de detalle para todos los horómetros
        for record in result:
            if not record.detalle_ids:
                horometros = self.env['mantenimientosx.horometro'].search([('active', '=', True)])
                for horometro in horometros:
                    # Aquí está el cambio clave: usamos horas_iniciales y horas_totales del horómetro
                    # para inicializar correctamente los valores
                    # Convertimos a enteros para eliminar los decimales
                    horas_iniciales = int(horometro.horas_iniciales)
                    horas_finales = int(horometro.horas_totales)
                    horas_promedio = int(horometro.horas_promedio or 0)
                    
                    self.env['mantenimientosx.horas.trabajadas.detalle'].create({
                        'horas_trabajadas_id': record.id,
                        'horometro_id': horometro.id,
                        'horas_iniciales': horas_iniciales,  # Usamos horas_iniciales del horómetro como entero
                        'horas_finales': horas_finales,      # Usamos horas_totales del horómetro como entero
                        'horas_promedio': horas_promedio,    # Inicializamos con el promedio del horómetro como entero
                    })
        
        return result
    
    @api.onchange('fecha')
    def _onchange_fecha(self):
        """Validar que la fecha no sea menor a la última registrada"""
        ultima_lectura = self.search([], order='fecha desc', limit=1)
        if ultima_lectura and self.fecha and self.fecha <= ultima_lectura.fecha:
            warning = {
                'title': _('Advertencia'),
                'message': _('La fecha no puede ser menor o igual a la última fecha registrada (%s).') % ultima_lectura.fecha,
            }
            return {'warning': warning}
    
    def action_confirmar(self):
        """Confirmar el registro de horas trabajadas"""
        for record in self:
            if record.state != 'borrador':
                continue
                
            # Asignar número de secuencia definitivo al confirmar
            if record.name == _('Nuevo'):
                record.name = self.env['ir.sequence'].next_by_code('mantenimientosx.horas.trabajadas') or _('Nuevo')
                
            # Validar que todas las líneas tengan horas finales mayores o iguales a las iniciales
            for linea in record.detalle_ids:
                if linea.horas_finales < linea.horas_iniciales:
                    raise ValidationError(_('Las horas finales no pueden ser menores a las horas iniciales para el horómetro %s.') % linea.horometro_id.name)
            
            # Actualizar horómetros
            for linea in record.detalle_ids:
                if linea.horas_trabajadas > 0:
                    # 1. Actualizar las Horas totales y Horas promedio de los Horómetros
                    linea.horometro_id.write({
                        'horas_totales': int(linea.horas_finales),  # Convertir a entero
                        'horas_promedio': int(linea.horas_promedio),  # Convertir a entero
                    })
                    
                    # Actualizar máquinas relacionadas con este horómetro
                    maquinas = self.env['mantenimientosx.maquina'].search([
                        ('horometro_id', '=', linea.horometro_id.id),
                        ('active', '=', True)
                    ])
                    
                    for maquina in maquinas:
                        # Actualizar horas totales y promedio en la máquina
                        maquina.write({
                            'horas_totales': int(linea.horas_finales),  # Convertir a entero
                            'horas_promedio': int(linea.horas_promedio),  # Convertir a entero
                        })
                        
                        # 2. Crear registros en el cronológico para cada actividad de la máquina
                        actividades = self.env['mantenimientosx.actividad.maquina'].search([
                            ('maquina_id', '=', maquina.id),
                            ('active', '=', True)
                        ])
                        
                        for actividad in actividades:
                            # Calcular campos para el cronológico y convertir a enteros
                            self.env['mantenimientosx.cronologico.maquina'].create({
                                'fecha': record.fecha,
                                'doc_id': record.name,
                                'maquina_id': maquina.id,
                                'categoria_id': maquina.categoria_id.id,
                                'horometro_id': linea.horometro_id.id,
                                'actividad_id': actividad.id,
                                'actividad': actividad.actividad,
                                'ultimo_mto': int(actividad.ultimo_mto) if actividad.ultimo_mto else 0,
                                'intervalo_mto': int(actividad.intervalo_mto) if actividad.intervalo_mto else 0,
                                'proximo_mto': int(actividad.proximo_mto) if actividad.proximo_mto else 0,
                                'horas_prox_mto': int(actividad.horas_prox_mto) if actividad.horas_prox_mto else 0,
                                'dias_prox_mto': int(actividad.dias_prox_mto) if actividad.dias_prox_mto else 0,
                                'dias_sig_mto': int(actividad.dias_sig_mto) if actividad.dias_sig_mto else 0,
                                'dias_para_planificacion': int(actividad.dias_para_planificacion) if actividad.dias_para_planificacion else 0,
                                'orden_pendiente': actividad.orden_pendiente,
                            })
                        
                        # Forzar el recálculo de los campos calculados de las actividades
                        for actividad in actividades:
                            # Si hay campos calculados en actividad.maquina que dependen de horas_totales o horas_promedio,
                            # forzamos su recálculo aquí
                            if hasattr(actividad, '_compute_proximo_mto'):
                                actividad._compute_proximo_mto()
                            # Añadir otros métodos de cálculo si existen
            
            record.write({'state': 'confirmado'})
    
    def action_borrador(self):
        """Volver a estado borrador"""
        for record in self:
            if record.state != 'confirmado':
                continue
            record.write({'state': 'borrador'})
            
    def action_cancelar(self):
        """Cancelar el registro y volver a la vista de lista"""
        # Si el registro ya está guardado en la base de datos, lo eliminamos
        if not self._context.get('no_delete') and self.id and self.name == _('Nuevo'):
            self.unlink()
            
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mantenimientosx.horas.trabajadas',
            'view_mode': 'tree,form',
            'target': 'current',
        }

class MantenimientosXHorasTrabajadasDetalle(models.Model):
    _name = 'mantenimientosx.horas.trabajadas.detalle'
    _description = 'Detalle de Horas Trabajadas'
    _order = 'horometro_id'
    
    horas_trabajadas_id = fields.Many2one('mantenimientosx.horas.trabajadas', 
                                         string='Horas Trabajadas', ondelete='cascade')
    horometro_id = fields.Many2one('mantenimientosx.horometro', string='Horómetro', required=True)
    horas_iniciales = fields.Integer(string='Horas iniciales', required=True)
    horas_finales = fields.Integer(string='Horas finales', required=True)
    horas_trabajadas = fields.Integer(string='Horas trabajadas', compute='_compute_horas_trabajadas', 
                                  store=True)
    horas_promedio = fields.Integer(string='Horas promedio')
    
    @api.depends('horas_iniciales', 'horas_finales')
    def _compute_horas_trabajadas(self):
        """Calcular horas trabajadas como la diferencia entre horas finales e iniciales"""
        for record in self:
            record.horas_trabajadas = max(0, record.horas_finales - record.horas_iniciales)
    
    @api.onchange('horas_finales')
    def _onchange_horas_finales(self):
        """
        Calcular horas trabajadas y validar que sean mayores o iguales a las iniciales.
        También calcula las horas promedio basado en los últimos 90 registros.
        """
        for record in self:
            if record.horas_finales < record.horas_iniciales:
                warning = {
                    'title': _('Advertencia'),
                    'message': _('Las horas finales no pueden ser menores a las horas iniciales.'),
                }
                return {'warning': warning}
            
            # Calcular horas promedio basado en los últimos 90 registros
            if record.horas_trabajadas > 0:
                # Buscar los últimos 90 registros para este horómetro
                ultimas_lecturas = self.search([
                    ('horometro_id', '=', record.horometro_id.id),
                    ('horas_trabajadas', '>', 0),
                    ('id', '!=', record.id if record.id else 0)
                ], limit=90, order='create_date desc')
                
                if ultimas_lecturas:
                    # Calcular el promedio incluyendo el registro actual
                    total_horas = sum(ultimas_lecturas.mapped('horas_trabajadas')) + record.horas_trabajadas
                    record.horas_promedio = int(total_horas / (len(ultimas_lecturas) + 1))  # Convertir a entero
                else:
                    # Si no hay registros previos, usar el promedio del horómetro
                    record.horas_promedio = int(record.horometro_id.horas_promedio or record.horas_trabajadas)  # Convertir a entero
