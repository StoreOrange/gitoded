# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from datetime import datetime, timedelta
import calendar
import logging
import io
import xlsxwriter

_logger = logging.getLogger(__name__)

class MantenimientosXExcelExport(http.Controller):
    
    @http.route('/mantenimientosx/excel_export', type='http', auth='user')
    def export_excel(self, **kw):
        """Exporta los datos del Gantt a Excel - Versión simplificada"""
        try:
            _logger.info("Iniciando exportación a Excel")
            
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
            
            _logger.info(f"Exportando datos desde {fecha_inicio} hasta {fecha_fin}")
            
            # Obtener datos del cronológico
            cronologico = request.env['mantenimientosx.cronologico.maquina'].search([
                ('fecha', '>=', fecha_inicio),
                ('fecha', '<=', fecha_fin)
            ], order='maquina_id, actividad')
            
            _logger.info(f"Encontrados {len(cronologico)} registros para exportar")
            
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
                'bg_color': '#71639e',
                'font_color': 'white',
                'border': 1
            })
            
            header_format = workbook.add_format({
                'bold': True,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#8a7cb8',
                'font_color': 'white',
                'border': 1
            })
            
            cell_format = workbook.add_format({
                'align': 'center',
                'valign': 'vcenter',
                'border': 1
            })
            
            # Título
            worksheet.merge_range(0, 0, 0, 9, 'Cronológico de Mantenimiento', title_format)
            worksheet.merge_range(1, 0, 1, 9, f'Período: {fecha_inicio.strftime("%d/%m/%Y")} - {fecha_fin.strftime("%d/%m/%Y")}', header_format)
            
            # Encabezados
            headers = ['Fecha', 'Documento', 'Máquina', 'Categoría', 'Horómetro', 'Actividad', 
                      'Último Mtto.', 'Intervalo Mtto.', 'Próximo Mtto.', 'Días para planificación']
            
            for col, header in enumerate(headers):
                worksheet.write(3, col, header, header_format)
            
            # Datos
            for row, record in enumerate(cronologico, start=4):
                worksheet.write(row, 0, record.fecha.strftime('%d/%m/%Y'), cell_format)
                worksheet.write(row, 1, record.doc_id or '', cell_format)
                worksheet.write(row, 2, record.maquina_id.name or '', cell_format)
                worksheet.write(row, 3, record.categoria_id.name or '', cell_format)
                worksheet.write(row, 4, record.horometro_id.name or '', cell_format)
                worksheet.write(row, 5, record.actividad or '', cell_format)
                worksheet.write(row, 6, record.ultimo_mto or 0, cell_format)
                worksheet.write(row, 7, record.intervalo_mto or 0, cell_format)
                worksheet.write(row, 8, record.proximo_mto or 0, cell_format)
                worksheet.write(row, 9, record.dias_para_planificacion or 0, cell_format)
            
            # Ajustar anchos de columna
            for col, width in enumerate([15, 15, 30, 20, 20, 40, 15, 15, 15, 20]):
                worksheet.set_column(col, col, width)
            
            workbook.close()
            
            # Preparar respuesta
            output.seek(0)
            filename = f'Cronologico_Mantenimiento_{fecha_inicio.strftime("%d-%m-%Y")}_{fecha_fin.strftime("%d-%m-%Y")}.xlsx'
            
            _logger.info(f"Archivo Excel generado: {filename}")
            
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
