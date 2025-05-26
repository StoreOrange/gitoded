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
        'views/mantenimientosx_menu.xml',
        'views/mantenimientosx_horometro_views.xml',
        
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}