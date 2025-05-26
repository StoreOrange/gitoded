from . import models

# Si necesitas importar controladores directamente, descomenta la siguiente línea
# from .models import mantenimientosx_gantt_controller

def post_init_hook(cr, registry):
    """
    Ejecuta acciones después de instalar el módulo.
    """
    from odoo import api, SUPERUSER_ID
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Restaurar parámetros del sistema para recuperar opciones de ajustes
    params = env['ir.config_parameter'].sudo()
    params.set_param('base.debug', 'true')
    params.set_param('base.technical_features', 'true')
    
    # Asegurarse de que los menús de ajustes estén activos
    settings_menu = env.ref('base.menu_administration', False)
    if settings_menu:
        settings_menu.write({'active': True})
    
    # Activar características técnicas para administradores
    admin_users = env['res.users'].search([('groups_id', 'in', env.ref('base.group_system').id)])
    for user in admin_users:
        if hasattr(user, 'technical_features'):
            user.write({'technical_features': True})
    
    # Verificar si el módulo de mantenimiento estándar está instalado
    maintenance_module = env['ir.module.module'].search([('name', '=', 'maintenance'), ('state', '=', 'installed')])
    if maintenance_module:
        # Registrar mensaje en el log
        import logging
        _logger = logging.getLogger(__name__)
        _logger.warning("El módulo de mantenimiento estándar está instalado. Esto puede causar conflictos con MantenimientosX.")
    
    # Forzar actualización de vistas
    env['ir.ui.view'].clear_caches()
    
    # Verificar que los menús existen
    menus = env['ir.ui.menu'].search([('name', '=', 'MantenimientosX')])
    if not menus:
        _logger.error("No se encontraron menús para MantenimientosX. Verificar la instalación.")
    else:
        _logger.info(f"Se encontraron {len(menus)} menús para MantenimientosX.")
