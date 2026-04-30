# Sistema de Administración de Propiedades Comerciales

## Pendientes

- [ ] Recrear el diagrama del esquema SQL al final del proyecto
- [ ] Notificar a inquilino y arrendador cuando un documento esté por vencer
- [ ] Migrar almacenamiento de archivos a la nube antes de salir a producción
- [ ] Revisar el nombre y formato de los archivos subidos (actualmente UUID)
- [ ] Implementar versionado de archivos — al actualizar un documento, guardar la versión anterior
    como v1, v2, etc. en lugar de eliminarlo
- [ ] Implementar notificaciones_log — registrar cada notificación enviada a inquilinos y arrendador
- [ ] Configurar SECRET_KEY como variable de entorno antes de salir a producción
- [ ] Evaluar portal para inquilinos — permitir que inquilinos accedan a sus documentos, 
    facturas y contrato desde la app (agregar rol inquilino a usuarios y asociarlo con inquilino_id)
- [x] Agregar manejo global de errores en src/__init__.py para errores inesperados de DB
- [x] Confirmar que el scheduler no requiere autenticación — llama a generate_invoice directamente
    sin pasar por una ruta
- [ ] Configurar nginx + SSL (Let's Encrypt) antes de salir a producción
- [ ] Actualizar todos los controllers para usar % formatting en lugar de f-strings en los logs
- [ ] Renombrar parámetro `id` a nombre específico en todas las rutas (ej. `unit_id`, `tenant_id`) 
    para evitar shadowing del built-in `id` de Python
- [ ] Botón "+ Nuevo" debe cambiar de texto al hacer click (ej. "Cancelar") y no redirigir — revisar 
    en todas las páginas
- [ ] En formulario de nuevo contrato, reemplazar campos de ID de unidad e inquilino por un selector 
    que cargue los registros existentes
- [ ] Agregar docstrings a todos los métodos de las rutas
- [ ] Verificar que acciones sensibles (crear usuario, desactivar usuario, eliminar registros) estén
    restringidas solo a roles admin y root — revisar en todas las rutas y en el frontend
- [ ] Pruebas completas de todas las funcionalidades — crear, editar, eliminar y visualizar 
    registros en cada sección