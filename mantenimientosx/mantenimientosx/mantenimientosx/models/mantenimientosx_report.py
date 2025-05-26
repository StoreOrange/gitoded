from odoo import models, fields, api
from datetime import datetime, timedelta
import calendar

class MantenimientosXReport(models.AbstractModel):
    _name = 'report.mantenimientosx.report_cronologico_gantt'
    _description = 'Reporte Cronológico de Mantenimiento'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Prepara los datos para el reporte de cronológico de mantenimiento"""
        # Obtener fechas del contexto o usar el mes actual
        fecha_inicio = data.get('fecha_inicio', datetime.today().replace(day=1).strftime('%Y-%m-%d'))
        ultimo_dia = calendar.monthrange(datetime.today().year, datetime.today().month)[1]
        fecha_fin = data.get('fecha_fin', datetime.today().replace(day=ultimo_dia).strftime('%Y-%m-%d'))
        
        # Convertir a objetos datetime
        fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d')
        fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d')
        
        # Generar lista de días para el encabezado
        dias = []
        current_date = fecha_inicio_dt
        while current_date <= fecha_fin_dt:
            dias.append({
                'numero': current_date.day,
                'dia_semana': current_date.strftime('%a'),  # Abreviatura del día de la semana
                'es_fin_semana': current_date.weekday() >= 5,  # 5 y 6 son sábado y domingo
                'fecha': current_date.strftime('%Y-%m-%d'),
            })
            current_date += timedelta(days=1)
        
        # Obtener registros de mantenimiento
        domain = [
            ('fecha', '>=', fecha_inicio),
            ('fecha', '<=', fecha_fin),
        ]
        
        # Si se especificaron máquinas específicas
        if data.get('maquina_ids'):
            domain.append(('maquina_id', 'in', data.get('maquina_ids')))
        
        # Obtener registros agrupados por banda y máquina
        registros = self.env['mantenimientosx.cronologico.maquina'].search(domain)
        
        # Agrupar por banda
        bandas = {}
        for registro in registros:
            banda_nombre = registro.banda or 'Sin Banda'
            if banda_nombre not in bandas:
                bandas[banda_nombre] = {
                    'nombre': banda_nombre,
                    'maquinas': {},
                }
            
            maquina_id = registro.maquina_id.id
            maquina_nombre = registro.maquina_id.name
            
            if maquina_id not in bandas[banda_nombre]['maquinas']:
                bandas[banda_nombre]['maquinas'][maquina_id] = {
                    'id': maquina_id,
                    'nombre': maquina_nombre,
                    'actividades': [],
                }
            
            # Añadir actividad
            bandas[banda_nombre]['maquinas'][maquina_id]['actividades'].append({
                'id': registro.id,
                'nombre': registro.actividad,
                'ultimo_mto': int(registro.ultimo_mto) if registro.ultimo_mto else 0,
                'intervalo_mto': int(registro.intervalo_mto) if registro.intervalo_mto else 0,
                'proximo_mto': int(registro.proximo_mto) if registro.proximo_mto else 0,
                'dias_prox_mto': registro.dias_prox_mto or 0,
                'horas_prox_mto': registro.horas_prox_mto or 0,
                'fecha_inicio': registro.fecha_inicio,
                'fecha_fin': registro.fecha_fin,
                'color': registro.color,
            })
        
        # Convertir diccionario a lista para la plantilla
        bandas_lista = []
        for banda_nombre, banda_data in bandas.items():
            maquinas_lista = []
            for maquina_id, maquina_data in banda_data['maquinas'].items():
                maquinas_lista.append({
                    'id': maquina_data['id'],
                    'nombre': maquina_data['nombre'],
                    'actividades': maquina_data['actividades'],
                })
            
            bandas_lista.append({
                'nombre': banda_data['nombre'],
                'maquinas': maquinas_lista,
            })
        
        return {
            'doc_ids': docids,
            'doc_model': 'mantenimientosx.cronologico.maquina',
            'docs': registros,
            'dias': dias,
            'bandas': bandas_lista,
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
        }
