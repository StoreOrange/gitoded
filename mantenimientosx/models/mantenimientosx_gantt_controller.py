# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from datetime import datetime, timedelta
import calendar
import logging
import io
import xlsxwriter
import locale

_logger = logging.getLogger(__name__)

class MantenimientosXGanttController(http.Controller):
    
    @http.route(['/mantenimientosx/excel_export', '/mantenimientosx/gantt/export'], type='http', auth='user', csrf=False)
    def export_excel(self, **kw):
        """Exporta los datos del Gantt a Excel - Versión que replica exactamente el diagrama de Gantt"""
        try:
            import io
            import xlsxwriter
            
            _logger.info("Iniciando exportación a Excel del diagrama de Gantt")
            
            # Obtener fechas del filtro
            fecha_inicio_str = kw.get('fecha_inicio', False)
            fecha_fin_str = kw.get('fecha_fin', False)
            
            try:
                fecha_inicio = datetime.strptime(fecha_inicio_str, '%d/%m/%Y').date()
                fecha_fin = datetime.strptime(fecha_fin_str, '%d/%m/%Y').date()
            except (ValueError, TypeError):
                # Si hay error en el formato, usar mes actual
                hoy = datetime.today()
                fecha_inicio = datetime(hoy.year, hoy.month, 1).date()
                ultimo_dia = calendar.monthrange(hoy.year, hoy.month)[1]
                fecha_fin = datetime(hoy.year, hoy.month, ultimo_dia).date()
            
            _logger.info(f"Exportando diagrama de Gantt desde {fecha_inicio} hasta {fecha_fin}")
            
            # Obtener los mismos datos que se usan en la vista web
            datos_cronologico = self._obtener_datos_cronologico(fecha_inicio, fecha_fin)
            dias = self._generar_dias(fecha_inicio, fecha_fin)
            meses = self._generar_meses(fecha_inicio, fecha_fin)
            
            _logger.info(f"Generando Excel con {len(datos_cronologico)} máquinas y {len(dias)} días")
            
            # Crear archivo Excel
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output)
            worksheet = workbook.add_worksheet('Cronológico de Mantenimiento')
            
            # Formatos
            title_format = workbook.add_format({
                'bold': True,
                'font_size': 16,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#71639e',  # Color púrpura
                'font_color': 'white',
                'border': 1
            })
            
            subtitle_format = workbook.add_format({
                'bold': True,
                'font_size': 12,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#5d5286',  # Tono más oscuro del púrpura
                'font_color': 'white',
                'border': 1
            })
            
            header_format = workbook.add_format({
                'bold': True,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#8a7cb8',  # Tono más claro del púrpura
                'font_color': 'white',
                'border': 1
            })
            
            day_header_format = workbook.add_format({
                'bold': True,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#8a7cb8',
                'font_color': 'white',
                'border': 1,
                'text_wrap': True
            })
            
            month_header_format = workbook.add_format({
                'bold': True,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#71639e',
                'font_color': 'white',
                'border': 1
            })
            
            maquina_format = workbook.add_format({
                'bold': True,
                'align': 'left',
                'valign': 'vcenter',
                'bg_color': '#edf2f7',
                'font_color': '#5d5286',
                'border': 1
            })
            
            actividad_format = workbook.add_format({
                'align': 'left',
                'valign': 'vcenter',
                'indent': 1,
                'border': 1
            })
            
            cell_format = workbook.add_format({
                'align': 'center',
                'valign': 'vcenter',
                'border': 1
            })
            
            # Estados
            estado_normal = workbook.add_format({
                'align': 'center',
                'valign': 'vcenter',
                'border': 1,
                'bg_color': '#2ecc71'  # Verde
            })
            
            estado_proximo = workbook.add_format({
                'align': 'center',
                'valign': 'vcenter',
                'border': 1,
                'bg_color': '#f1c40f'  # Amarillo
            })
            
            estado_atrasado = workbook.add_format({
                'align': 'center',
                'valign': 'vcenter',
                'border': 1,
                'bg_color': '#e74c3c'  # Rojo
            })
            
            estado_pendiente = workbook.add_format({
                'align': 'center',
                'valign': 'vcenter',
                'border': 1,
                'bg_color': '#3498db'  # Azul
            })
            
            # Título del reporte
            worksheet.merge_range(0, 0, 0, 5 + len(dias), 'Cronológico de Mantenimiento', title_format)
            
            # Subtítulo con fechas
            fecha_rango = f"Del {fecha_inicio.strftime('%d/%m/%Y')} al {fecha_fin.strftime('%d/%m/%Y')}"
            worksheet.merge_range(1, 0, 1, 5 + len(dias), fecha_rango, subtitle_format)
            
            # Encabezados de columnas fijas (corregidos según la imagen)
            worksheet.write(3, 0, 'Máquinas/Actividades', header_format)
            worksheet.write(3, 1, 'Último Mtto.', header_format)
            worksheet.write(3, 2, 'Intervalo Mtto.', header_format)
            worksheet.write(3, 3, 'Próximo Mtto.', header_format)
            worksheet.write(3, 4, 'Días Próx. Mtto.', header_format)
            worksheet.write(3, 5, 'Días Sig. Mtto.', header_format)
            
            # Encabezados de meses con "Horas Próx. Mtto."
            col_offset = 6
            for mes in meses:
                # Crear encabezado con "Horas Próx. Mtto." + mes
                mes_header = f"Horas Próx. Mtto. {mes['nombre']}"
                col_inicio = col_offset
                col_fin = col_inicio + mes['dias'] - 1
                worksheet.merge_range(2, col_inicio, 2, col_fin, mes_header, month_header_format)
                col_offset += mes['dias']
            
            # Encabezados de días
            for i, dia in enumerate(dias):
                col = i + 5 + 1
                # Número de día
                worksheet.write(3, col, dia['numero'], day_header_format)
                # Día de la semana abreviado
                worksheet.write(4, col, dia['dia_semana'], day_header_format)
            
            # Datos
            row = 5
            for maquina in datos_cronologico:
                # Escribir nombre de la máquina
                worksheet.write(row, 0, maquina['nombre'], maquina_format)
                worksheet.merge_range(row, 1, row, 5, '', maquina_format)
                
                # Días vacíos para la fila de la máquina
                for i in range(len(dias)):
                    worksheet.write(row, i + 6, '', maquina_format)
                
                row += 1
                
                # Actividades
                for actividad in maquina['actividades']:
                    worksheet.write(row, 0, actividad['nombre'], actividad_format)
                    worksheet.write(row, 1, actividad['ultimo_mto'], cell_format)
                    worksheet.write(row, 2, actividad['intervalo_mto'], cell_format)
                    worksheet.write(row, 3, actividad['proximo_mto'], cell_format)
                    worksheet.write(row, 4, actividad['dias_prox_mto'], cell_format)
                    worksheet.write(row, 5, actividad['dias_sig_mto'], cell_format)
                    
                    # Días - Mostrar horas_prox_mto en cada celda
                    for i, dia in enumerate(dias):
                        col = i + 6
                        fecha = dia['fecha']
                        
                        if fecha in actividad['fechas']:
                            estado = actividad['fechas'][fecha]['estado']
                            # Usar horas_prox_mto en lugar de doc_id
                            valor = actividad['horas_prox_mto']
                            
                            if estado == 'normal':
                                worksheet.write(row, col, valor, estado_normal)
                            elif estado == 'proximo':
                                worksheet.write(row, col, valor, estado_proximo)
                            elif estado == 'atrasado':
                                worksheet.write(row, col, valor, estado_atrasado)
                            elif estado == 'pendiente':
                                worksheet.write(row, col, valor, estado_pendiente)
                        else:
                            worksheet.write(row, col, '', cell_format)
                    
                    row += 1
            
            # Leyenda
            row += 2
            worksheet.merge_range(row, 0, row, 5 + len(dias), 'Leyenda', subtitle_format)
            row += 1
            
            worksheet.write(row, 0, 'Normal', estado_normal)
            worksheet.write(row, 1, 'Próximo (menos de 7 días)', estado_proximo)
            worksheet.write(row, 2, 'Atrasado', estado_atrasado)
            worksheet.write(row, 3, 'Orden Pendiente', estado_pendiente)
            
            # Pie de página
            row += 2
            fecha_generacion = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            worksheet.merge_range(row, 0, row, 5 + len(dias), f'Generado el: {fecha_generacion}', cell_format)
            
            # Ajustar anchos de columna
            worksheet.set_column(0, 0, 30)  # Máquinas/Actividades
            worksheet.set_column(1, 5, 15)  # Columnas de datos
            worksheet.set_column(6, 6 + len(dias) - 1, 5)  # Días
            
            # Ajustar altura de filas
            worksheet.set_row(2, 30)  # Fila de meses
            worksheet.set_row(3, 20)  # Fila de días (números)
            worksheet.set_row(4, 20)  # Fila de días (nombres)
            
            # Congelar paneles para mejor navegación
            worksheet.freeze_panes(5, 6)
            
            workbook.close()
            
            # Preparar respuesta
            output.seek(0)
            filename = f'Cronologico_Mantenimiento_{fecha_inicio.strftime("%d-%m-%Y")}_{fecha_fin.strftime("%d-%m-%Y")}.xlsx'
            
            _logger.info(f"Archivo Excel del diagrama de Gantt generado: {filename}")
            
            # Configurar headers para forzar la descarga
            headers = [
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', f'attachment; filename="{filename}"'),
                ('Content-Length', str(len(output.getvalue()))),
                ('Cache-Control', 'no-cache, no-store, must-revalidate'),
                ('Pragma', 'no-cache'),
                ('Expires', '0')
            ]
            
            return request.make_response(output.getvalue(), headers=headers)
            
        except Exception as e:
            import traceback
            _logger.error(f"Error en export_excel: {e}\n{traceback.format_exc()}")
            return request.render('web.http_error', {
                'status_code': 500,
                'status_message': f"Error al exportar a Excel: {str(e)}"
            })
    
    @http.route('/mantenimientosx/gantt', type='http', auth='user')
    def gantt_view(self, **kw):
        try:
            # Intentar configurar el locale para español
            try:
                locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
            except:
                try:
                    locale.setlocale(locale.LC_TIME, 'es_ES')
                except:
                    _logger.warning("No se pudo configurar el locale a español")
            
            # Obtener fechas del filtro o usar el mes actual por defecto
            fecha_inicio_str = kw.get('fecha_inicio', False)
            fecha_fin_str = kw.get('fecha_fin', False)
            
            if fecha_inicio_str and fecha_fin_str:
                try:
                    fecha_inicio = datetime.strptime(fecha_inicio_str, '%d/%m/%Y').date()
                    fecha_fin = datetime.strptime(fecha_fin_str, '%d/%m/%Y').date()
                except ValueError:
                    # Si hay error en el formato, usar mes actual
                    hoy = datetime.today()
                    fecha_inicio = datetime(hoy.year, hoy.month, 1).date()
                    ultimo_dia = calendar.monthrange(hoy.year, hoy.month)[1]
                    fecha_fin = datetime(hoy.year, hoy.month, ultimo_dia).date()
            else:
                # Usar mes actual por defecto
                hoy = datetime.today()
                fecha_inicio = datetime(hoy.year, hoy.month, 1).date()
                ultimo_dia = calendar.monthrange(hoy.year, hoy.month)[1]
                fecha_fin = datetime(hoy.year, hoy.month, ultimo_dia).date()
            
            # Obtener datos agrupados por máquina y actividad
            datos_cronologico = self._obtener_datos_cronologico(fecha_inicio, fecha_fin)
            
            # Obtener información de menús para la navegación
            menu_tablero = request.env.ref('mantenimientosx.menu_mantenimientosx_tablero', False)
            
            # Preparar datos para la vista
            valores = {
                'fecha_inicio': fecha_inicio.strftime('%d/%m/%Y'),
                'fecha_fin': fecha_fin.strftime('%d/%m/%Y'),
                'datos_cronologico': datos_cronologico,
                'dias': self._generar_dias(fecha_inicio, fecha_fin),
                'meses': self._generar_meses(fecha_inicio, fecha_fin),
                # Añadir información de menús
                'menu_tablero': menu_tablero and menu_tablero.id or False,
                # Añadir idiomas para evitar el error de NoneType
                'languages': [],
                # Añadir módulo datetime para usar en la plantilla
                'datetime': datetime,
                # Estadísticas
                'total_maquinas': len(datos_cronologico),
                'total_actividades': sum(len(m['actividades']) for m in datos_cronologico),
                'total_mantenimientos': self._contar_mantenimientos(datos_cronologico),
            }
            
            return request.render('mantenimientosx.gantt_template', valores)
        except Exception as e:
            _logger.error(f"Error en gantt_view: {e}", exc_info=True)
            return request.render('web.http_error', {
                'status_code': 500,
                'status_message': f"Error interno: {str(e)}"
            })
    
    def _contar_mantenimientos(self, datos_cronologico):
        """Cuenta el número total de mantenimientos en el período"""
        total = 0
        for maquina in datos_cronologico:
            for actividad in maquina['actividades']:
                total += len(actividad['fechas'])
        return total
    
    def _obtener_datos_cronologico(self, fecha_inicio, fecha_fin):
        """Obtiene los datos del cronológico agrupados por máquina y actividad"""
        try:
            # Obtener registros del cronológico
            registros = request.env['mantenimientosx.cronologico.maquina'].search([
                ('fecha', '>=', fecha_inicio),
                ('fecha', '<=', fecha_fin)
            ], order='maquina_id, actividad')
            
            # Agrupar por máquina
            datos_agrupados = {}
            for registro in registros:
                maquina_id = registro.maquina_id.id
                maquina_nombre = registro.maquina_id.name
                
                if maquina_id not in datos_agrupados:
                    datos_agrupados[maquina_id] = {
                        'nombre': maquina_nombre,
                        'actividades': {}
                    }
                
                # Agrupar por actividad
                actividad_id = registro.actividad_id.id if registro.actividad_id else 0
                actividad_nombre = registro.actividad or 'Sin actividad'
                
                if actividad_id not in datos_agrupados[maquina_id]['actividades']:
                    datos_agrupados[maquina_id]['actividades'][actividad_id] = {
                        'nombre': actividad_nombre,
                        'ultimo_mto': registro.ultimo_mto,
                        'intervalo_mto': registro.intervalo_mto,
                        'proximo_mto': registro.proximo_mto,
                        'horas_prox_mto': registro.horas_prox_mto,
                        'dias_prox_mto': registro.dias_prox_mto,
                        'dias_sig_mto': registro.dias_sig_mto,
                        'dias_para_planificacion': registro.dias_para_planificacion,
                        'orden_pendiente': registro.orden_pendiente,
                        'fechas': {}
                    }
                
                # Registrar la fecha
                fecha_str = registro.fecha.strftime('%Y-%m-%d')
                datos_agrupados[maquina_id]['actividades'][actividad_id]['fechas'][fecha_str] = {
                    'estado': self._determinar_estado(registro),
                    'doc_id': registro.doc_id,
                    'horas_prox_mto': registro.horas_prox_mto  # Añadir horas_prox_mto para mostrar en las celdas
                }
            
            # Convertir a lista para la plantilla
            resultado = []
            for maquina_id, maquina_data in datos_agrupados.items():
                maquina_item = {
                    'id': maquina_id,
                    'nombre': maquina_data['nombre'],
                    'actividades': []
                }
                
                for actividad_id, actividad_data in maquina_data['actividades'].items():
                    maquina_item['actividades'].append({
                        'id': actividad_id,
                        'nombre': actividad_data['nombre'],
                        'ultimo_mto': actividad_data['ultimo_mto'],
                        'intervalo_mto': actividad_data['intervalo_mto'],
                        'proximo_mto': actividad_data['proximo_mto'],
                        'horas_prox_mto': actividad_data['horas_prox_mto'],
                        'dias_prox_mto': actividad_data['dias_prox_mto'],
                        'dias_sig_mto': actividad_data['dias_sig_mto'],
                        'dias_para_planificacion': actividad_data['dias_para_planificacion'],
                        'orden_pendiente': actividad_data['orden_pendiente'],
                        'fechas': actividad_data['fechas']
                    })
                
                resultado.append(maquina_item)
            
            return resultado
        except Exception as e:
            _logger.error(f"Error en _obtener_datos_cronologico: {e}", exc_info=True)
            return []
    
    def _determinar_estado(self, registro):
        """Determina el estado para colorear la celda en el Gantt"""
        # Lógica para determinar el estado según los datos del registro
        # Por ejemplo, basado en días para planificación
        if registro.dias_para_planificacion and registro.dias_para_planificacion < 0:
            return 'atrasado'  # Rojo
        elif registro.dias_para_planificacion and registro.dias_para_planificacion < 7:
            return 'proximo'   # Amarillo
        elif registro.orden_pendiente:
            return 'pendiente' # Azul
        else:
            return 'normal'    # Verde
    
    def _generar_dias(self, fecha_inicio, fecha_fin):
        """Genera la lista de días para el encabezado del Gantt"""
        dias = []
        fecha_actual = fecha_inicio
        
        while fecha_actual <= fecha_fin:
            dias.append({
                'numero': fecha_actual.day,
                'fecha': fecha_actual.strftime('%Y-%m-%d'),
                'dia_semana': self._obtener_dia_semana(fecha_actual.weekday())
            })
            fecha_actual += timedelta(days=1)
        
        return dias
    
    def _generar_meses(self, fecha_inicio, fecha_fin):
        """Genera la lista de meses para el encabezado del Gantt"""
        meses = []
        fecha_actual = fecha_inicio
        
        while fecha_actual <= fecha_fin:
            # Intentar usar el nombre del mes en español
            try:
                mes = fecha_actual.strftime('%B %Y').capitalize()
            except:
                # Si falla, usar el nombre en inglés
                mes_nombres = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                              'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
                mes = f"{mes_nombres[fecha_actual.month - 1]} {fecha_actual.year}"
            
            if not meses or meses[-1]['nombre'] != mes:
                meses.append({
                    'nombre': mes,
                    'dias': 0
                })
            
            meses[-1]['dias'] += 1
            fecha_actual += timedelta(days=1)
        
        return meses
    
    def _obtener_dia_semana(self, dia_numero):
        """Convierte el número de día de la semana a texto abreviado"""
        dias = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
        return dias[dia_numero]
