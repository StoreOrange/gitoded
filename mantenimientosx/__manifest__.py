{
    'name': 'MantenimientosX',
    'version': '1.0',
    'category': 'Maintenance',
    'summary': 'Gestión de mantenimientos básicos',
    'description': """
        Módulo básico para gestionar mantenimientos con una interfaz simple.
        Incluye tablero, solicitudes, equipos y configuraciones.
    """,
    'author': 'Usuario',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/mantenimientosx_config_views.xml',
        'views/mantenimientosx_views.xml',
        'views/mantenimientosx_horometro_views.xml',
        'views/mantenimientosx_tipo_mantenimiento_views.xml',
        'views/mantenimientosx_maquina_views.xml',
        'views/mantenimientosx_actividad_maquina_views.xml',
        'views/mantenimientosx_horas_trabajadas_views.xml',
        'views/mantenimientosx_historico_maquina_views.xml',
        'views/mantenimientosx_gantt_template.xml',
        'views/mantenimientosx_gantt_views.xml',
        'views/mantenimientosx_gantt_integration.xml',
        'views/mantenimientosx_menu.xml',
        
        
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}