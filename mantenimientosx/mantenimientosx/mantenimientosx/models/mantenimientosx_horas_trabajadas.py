# -*- coding: utf-8 -*-

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
    is_latest_record = fields.Boolean(string='Es el registro más reciente', compute='_compute_is_latest_record', store=False)
    
    @api.depends('fecha')
    def _compute_is_latest_record(self):
        """Determina si este es el registro con la fecha más reciente"""
        ultima_fecha = self.search([], order='fecha desc', limit=1).fecha
        for record in self:
            record.is_latest_record = record.fecha and ultima_fecha and record.fecha >= ultima_fecha
    
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
        2. Si no hay registros pero hay horómetros, usar la fecha actual
        3. Si no hay nada, la fecha actual
        """
        # Buscar la última lectura de horas trabajadas
        ultima_lectura = self.search([], order='fecha desc', limit=1)
        if ultima_lectura:
            return ultima_lectura.fecha + timedelta(days=1)
        
        # Si no hay lecturas previas, usar la fecha actual
        return fields.Date.context_today(self)
    
    @api.model
    def default_get(self, fields_list):
        """
        Sobrescribimos default_get para cargar los horómetros automáticamente
        cuando se crea un nuevo registro desde la interfaz
        """
        res = super(MantenimientosXHorasTrabajadas, self).default_get(fields_list)
        
        # Si estamos creando un nuevo registro, preparamos las líneas de detalle
        if 'detalle_ids' in fields_list:
            detalle_vals = []
            horometros = self.env['mantenimientosx.horometro'].search([('active', '=', True)])
            
            if horometros:
                for horometro in horometros:
                    # Verificamos que el horómetro tenga un ID válido
                    if horometro.id:
                        # Convertimos a enteros para eliminar los decimales
                        horas_iniciales = int(horometro.horas_totales)
                        # Inicializamos horas_finales con el mismo valor que horas_iniciales
                        horas_promedio = int(horometro.horas_promedio or 0)
                        
                        detalle_vals.append((0, 0, {
                            'horometro_id': horometro.id,
                            'horas_iniciales': horas_iniciales,
                            'horas_finales': 0,  # Inicializar con cero en lugar de horas_iniciales
                            'horas_promedio': horas_promedio,
                        }))
            
            # Solo asignamos detalle_vals si estamos dentro del bloque condicional
            res['detalle_ids'] = detalle_vals
        
        return res
    
    @api.model
    def create(self, vals):
        """Al crear, asignamos automáticamente los horómetros si no se han cargado ya"""
        # Asignar número de secuencia si es nuevo
        if vals.get('name', _('Nuevo')) == _('Nuevo'):
            vals['name'] = self.env['ir.sequence'].next_by_code('mantenimientosx.horas.trabajadas') or _('Nuevo')
        
        # Si no hay detalle_ids en vals o está vacío, los cargamos
        if 'detalle_ids' not in vals or not vals.get('detalle_ids'):
            detalle_vals = []
            horometros = self.env['mantenimientosx.horometro'].search([('active', '=', True)])
            
            if not horometros:
                raise ValidationError(_('No hay horómetros activos en el sistema. Por favor, cree al menos un horómetro antes de continuar.'))
            
            for horometro in horometros:
                # Convertimos a enteros para eliminar los decimales
                horas_iniciales = int(horometro.horas_totales)
                # Dejamos horas_finales vacías para que el usuario las complete
                horas_promedio = int(horometro.horas_promedio or 0)
                
                detalle_vals.append((0, 0, {
                    'horometro_id': horometro.id,
                    'horas_iniciales': horas_iniciales,
                    'horas_finales': 0,  # Inicializar con cero en lugar de horas_iniciales
                    'horas_promedio': horas_promedio,
                }))
            
            # Solo asignamos detalle_vals si se ha definido dentro del bloque condicional
            vals['detalle_ids'] = detalle_vals
        
        return super(MantenimientosXHorasTrabajadas, self).create(vals)
    
    def _cargar_horometros(self):
        """Método auxiliar para cargar los horómetros"""
        self.ensure_one()
        
        # Eliminar líneas existentes si las hay
        if self.detalle_ids:
            self.detalle_ids.unlink()
        
        horometros = self.env['mantenimientosx.horometro'].search([('active', '=', True)])
        
        # Verificar que existan horómetros
        if not horometros:
            raise ValidationError(_('No hay horómetros activos en el sistema. Por favor, cree al menos un horómetro antes de continuar.'))
        
        detalle_vals = []
        for horometro in horometros:
            # Verificar que el horómetro tenga un ID válido
            if horometro.id:
                # Convertimos a enteros para eliminar los decimales
                horas_iniciales = int(horometro.horas_totales)
                # Dejamos horas_finales vacías para que el usuario lo complete
                horas_promedio = int(horometro.horas_promedio or 0)
                
                detalle_vals.append((0, 0, {
                    'horometro_id': horometro.id,
                    'horas_iniciales': horas_iniciales,
                    'horas_finales': 0,  # Debe iniciar en cero para que el usuario lo llene manualmente
                    'horas_promedio': horas_promedio,
                }))
        
        if detalle_vals:
            self.write({'detalle_ids': detalle_vals})
    
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
        # Confirmar el registro de horas trabajadas
        for record in self:
            if record.state != 'borrador':
                continue
            try:
                # Asignar número de secuencia definitivo al confirmar
                if record.name == _('Nuevo'):
                    record.name = self.env['ir.sequence'].next_by_code('mantenimientosx.horas.trabajadas') or _('Nuevo')

                # Validar que todas las líneas tengan horas válidas
                for linea in record.detalle_ids:
                    if linea.horas_finales <= 0:
                        raise ValidationError(_('Las horas finales deben ser mayores a cero para el horómetro %s.') % linea.horometro_id.name)
                    if linea.horas_finales < linea.horas_iniciales:
                        raise ValidationError(_('Las horas finales no pueden ser menores a las horas iniciales para el horómetro %s.') % linea.horometro_id.name)

                # Actualizar horómetros, máquinas y crear cronológicos
                for linea in record.detalle_ids:
                    if linea.horas_trabajadas > 0:
                        # 1. Actualizar el horómetro
                        linea.horometro_id.write({
                            'horas_totales': int(linea.horas_finales),
                            'horas_promedio': int(linea.horas_promedio),
                        })

                        # 2. Actualizar máquinas relacionadas
                        maquinas = self.env['mantenimientosx.maquina'].search([
                            ('horometro_id', '=', linea.horometro_id.id),
                            ('active', '=', True)
                        ])
                        for maquina in maquinas:
                            maquina.write({
                                'horas_totales': int(linea.horas_finales),
                                'horas_promedio': int(linea.horas_promedio),
                            })

                            # 3. Crear registros cronológicos
                            actividades = self.env['mantenimientosx.actividad.maquina'].search([
                                ('maquina_id', '=', maquina.id),
                                ('active', '=', True)
                            ])
                            for actividad in actividades:
                                self.env['mantenimientosx.cronologico.maquina'].create({
                                    'fecha': record.fecha,
                                    'doc_id': record.name,
                                    'maquina_id': maquina.id,
                                    'categoria_id': maquina.categoria_id.id,
                                    'horometro_id': linea.horometro_id.id,
                                    'actividad_id': actividad.id,
                                    'actividad': actividad.actividad,
                                    'ultimo_mto': int(actividad.ultimo_mto or 0),
                                    'intervalo_mto': int(actividad.intervalo_mto or 0),
                                    'proximo_mto': int(actividad.proximo_mto or 0),
                                    'horas_prox_mto': int(actividad.horas_prox_mto or 0),
                                    'dias_prox_mto': int(actividad.dias_prox_mto or 0),
                                    'dias_sig_mto': int(actividad.dias_sig_mto or 0),
                                    'dias_para_planificacion': int(actividad.dias_para_planificacion or 0),
                                    'orden_pendiente': actividad.orden_pendiente,
                                })

                            # Forzar recálculo de actividad
                            for actividad in actividades:
                                actividad._compute_proximo_mto()
                                actividad._compute_campos_calculados()

                # ✅ Cálculo manual de horas promedio solo al confirmar
                for linea in record.detalle_ids:
                    if linea.horas_trabajadas > 0:
                        linea._calcular_horas_promedio()

                record.write({'state': 'confirmado'})

                return {
                    'type': 'ir.actions.client',
                    'tag': 'reload',
                }

            except Exception as e:
                _logger.error(f"Error al confirmar horas trabajadas: {e}")
                raise ValidationError(_(f"Error al confirmar: {e}"))

    
    def action_restablecer_borrador(self):
        """
        Restablecer a estado borrador para el registro más reciente.
        Solo las horas finales serán editables nuevamente.
        """
        self.ensure_one()
        
        # Verificar que sea el registro más reciente
        ultima_lectura = self.search([], order='fecha desc', limit=1)
        if self.id != ultima_lectura.id:
            raise UserError(_('Solo se puede restablecer a borrador el registro más reciente.'))
        
        # Eliminar registros cronológicos asociados a este documento
        registros_cronologicos = self.env['mantenimientosx.cronologico.maquina'].search([
            ('doc_id', '=', self.name),
            ('fecha', '=', self.fecha)
        ])
        if registros_cronologicos:
            registros_cronologicos.unlink()
            
        # Volver a estado borrador
        self.write({'state': 'borrador'})
        
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
    
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
    
    # Método para crear un horómetro de prueba si no existe ninguno
    @api.model
    def crear_horometro_prueba(self):
        """Crea un horómetro de prueba si no existe ninguno"""
        horometros = self.env['mantenimientosx.horometro'].search([])
        if not horometros:
            try:
                self.env['mantenimientosx.horometro'].create({
                    'name': 'Horómetro de Prueba',
                    'horas_iniciales': 0,
                    'horas_totales': 0,
                    'horas_promedio': 0,
                    'active': True,
                })
                return True
            except Exception as e:
                _logger.error(f"Error al crear horómetro de prueba: {e}")
                return False
        return True

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
        Mostrar advertencia si las horas finales son menores a las iniciales,
        pero permitir guardar para que el usuario pueda continuar editando.
        """
        for record in self:
            if record.horas_finales < record.horas_iniciales:
                return {
                    'warning': {
                        'title': _('Advertencia'),
                        'message': _('Las horas finales no deberían ser menores a las horas iniciales. Este valor será validado al confirmar.'),
                    }
                }

    @api.constrains('horas_finales', 'horas_iniciales')
    def _check_horas_finales(self):
        """
        No validamos aquí, solo al confirmar.
        La validación se hará en el método action_confirmar del modelo principal.
        """
        pass

    @api.model
    def create(self, vals):
        """Al crear, calculamos las horas trabajadas pero no el promedio"""
        _logger.info(f"Creando detalle de horas trabajadas con valores: {vals}")
        
        # Asegurarnos de que horometro_id y horas_iniciales estén presentes
        if 'horometro_id' not in vals or not vals.get('horometro_id'):
            _logger.warning("Advertencia: No se proporcionó un horómetro, intentando buscar uno por defecto")
            horometro_default = self.env['mantenimientosx.horometro'].search([], limit=1)
            if horometro_default:
                vals['horometro_id'] = horometro_default.id
            else:
                raise ValidationError(_('No se encontró ningún horómetro. Por favor, cree al menos uno antes de continuar.'))
        
        # Asegurarnos de que horas_iniciales esté presente
        if 'horas_iniciales' not in vals or vals.get('horas_iniciales') is None:
            _logger.warning("Advertencia: No se proporcionaron horas iniciales, estableciendo a 0")
            vals['horas_iniciales'] = 0
        
        # Asegurarnos de que horas_finales esté presente
        if 'horas_finales' not in vals or vals.get('horas_finales') is None:
            _logger.warning("Advertencia: No se proporcionaron horas finales, estableciendo a 0")
            vals['horas_finales'] = 0
        
        try:
            res = super(MantenimientosXHorasTrabajadasDetalle, self).create(vals)
            _logger.info(f"Detalle creado con éxito: {res.id}")
            return res
        except Exception as e:
            _logger.error(f"Error al crear detalle: {e}")
            raise ValidationError(_(f"Error al crear detalle: {e}"))

    def write(self, vals):
        """Al actualizar, calculamos las horas promedio solo si se han modificado las horas finales"""
        res = super(MantenimientosXHorasTrabajadasDetalle, self).write(vals)
        
        # Si se modificaron las horas finales, calculamos el promedio
        if 'horas_finales' in vals:
            self._calcular_horas_promedio()
        
        return res

    def _calcular_horas_promedio(self):
     """
       Calcula las horas promedio basado en los últimos 90 registros confirmados
        con horas trabajadas > 0, para el mismo horómetro.

        Si no hay registros previos, usa el valor del horómetro como base.
        """
     for record in self:
        if record.horas_trabajadas > 0:
            detalle_model = self.env['mantenimientosx.horas.trabajadas.detalle']

            # Buscar todos los detalles confirmados (sin ordenar aún)
            detalles_anteriores = detalle_model.search([
                ('horometro_id', '=', record.horometro_id.id),
                ('horas_trabajadas', '>', 0),
                ('id', '!=', record.id),
                ('horas_trabajadas_id.state', '=', 'confirmado')
            ])

            # Ordenar manualmente por fecha descendente del registro principal
            detalles_anteriores = sorted(
                detalles_anteriores,
                key=lambda d: d.horas_trabajadas_id.fecha or fields.Date.today(),
                reverse=True
            )[:90]

            if detalles_anteriores:
                total_horas = sum(d.horas_trabajadas for d in detalles_anteriores) + record.horas_trabajadas
                total_registros = len(detalles_anteriores) + 1
                record.horas_promedio = int(total_horas / total_registros)
            else:
                record.horas_promedio = int(record.horometro_id.horas_promedio or record.horas_trabajadas)


