# Sistema de Administración de Propiedades Comerciales

## Pendientes

- [x]  Recrear el diagrama del esquema SQL al final del proyecto
- [x] Agregar manejo global de errores en src/__init__.py para errores inesperados de DB
- [x] Confirmar que el scheduler no requiere autenticación — llama a generate_invoice directamente 
    sin pasar por una ruta
- [x] Bug lógico: usuario root podía ser desactivado por cualquier admin — se agregó guarda en 
    `deactivate_user` que lanza `ValueError` si el rol es `root`
- [x] Bug: `area_m2` y `renta_base` en unidades aceptaban valores negativos — se agregó validación 
    `> 0` en `create_unit` y `update_unit`
- [x] Bug: ruta PUT de unidades no atrapaba `ValueError` del controller — se agregó try/except en 
    `modify_unit`
- [x] Bug: `dia_cobro` no tenía validación en el controller — se agregó validación 
    `BETWEEN 1 AND 28` en `create_contract` y `update_contract`
- [x] Verificar try/except para `ValueError` en todas las rutas PUT/PATCH — `modify_tenant` 
    faltaba try/except; `modify_maintenance` y `modify_document` ya lo tenían correcto
- [x] Actualizar todos los controllers para usar % formatting en lugar de f-strings en los logs
- [x] Renombrar parámetro `id` a nombre específico en todas las rutas y controllers
- [x] Agregar docstrings a todos los métodos de las rutas
- [x] Agregar module docstring a todos los controllers
- [x] Botón "+ Nuevo" cambia de texto al hacer click en todas las páginas — formulario se resetea 
    al cancelar
- [x] Configurar SECRET_KEY como variable de entorno — app lanza RuntimeError si no está definida; 
    se carga desde .env con python-dotenv
- [x] Implementar páginas de error HTML para 404 y 500
- [x] Verificar permisos por rol — rutas protegidas con require_auth y require_admin; 
    logout cambiado a POST con CSRF token
- [x] `numero` de unidad ahora se genera automáticamente con formato `{PREFIX}-{NNN}` según el tipo
- [x] Notificaciones en app — bell en topbar muestra documentos por vencer y facturas vencidas
- [x] Revisar el nombre y formato de los archivos subidos — UUID con extensión original

## Pruebas pendientes

- [ ] Unidades — crear, ver detalle, editar
  - [ ] Pregunta de negocio: cambiar `estado` manualmente no está vinculado al contrato activo — definir si debe bloquearse, lanzar advertencia, o solo actualizar el estado
- [ ] Inquilinos — crear, ver detalle, editar
  - [x] Bug: falta validación en `correo`, `telefono` y `rfc` — validación agregada en controller y frontend
  - [x] Bug lógico: el inquilino no expone un ID visible en la UI — se agregó campo ID en la vista de detalle y en la tabla
  - [x] Bug: la BD tenía UNIQUE constraint en `correo` — eliminado en migración
  - [x] UI: campos RFC y Creado se renderizan en dos líneas — corregido ajustando anchos de columna
- [ ] Contratos — crear, ver detalle, editar, terminar
  - [x] Bug: campos ID Unidad e ID Inquilino aceptaban entrada manual — reemplazados por selectores
  - [x] Bug: no se validaba que la unidad o el inquilino existan antes de crear el contrato — validación agregada en controller
  - [x] UI: las fechas `fecha_inicio` y `fecha_fin` se renderizan en dos líneas — corregido
- [ ] Facturas — verificar generación automática por scheduler, registrar pago
  - [x] Scheduler verificado — genera facturas correctamente en `dia_cobro`
  - [x] Registro de pago implementado en UI
  - [x] Alerta de facturas vencidas en página de facturas y en notificaciones
- [ ] Mantenimientos — crear, actualizar estado, resolver
  - [x] Bug: `unidad_id` era campo de texto libre — reemplazado por selector
  - [x] UI: colores agregados a `prioridad` — escala verde → azul → amarillo → rojo
  - [x] Bug lógico: `descripcion` implementado como journal acumulativo con fecha automática
  - [x] Contrato activo capturado al momento de crear el mantenimiento
- [ ] Documentos — subir archivo, verificar que se guarda correctamente
  - [x] Bug lógico: FKs reemplazados por selectores; los tres son requeridos
  - [x] Bug lógico: opción de eliminar documento implementada
  - [x] Enlaces de descarga firmados (tokens_descarga) — válidos 7 días, no requieren autenticación
- [ ] Usuarios — crear usuario staff, desactivar, reactivar
  - [ ] Pruebas de permisos pendientes por rol:
    - **Sin sesión:** acceder a cualquier ruta protegida debe devolver 401 o redirigir a login
    - **Staff:** puede ver y editar todo, puede eliminar documentos — no puede gestionar usuarios
    - **Admin:** todo lo anterior más gestión de usuarios — no puede desactivar a root
    - **Root:** acceso total — no puede ser desactivado

## Seguridad

- [x] Bandit — 0 issues reales (7 falsos positivos suprimidos con `# nosec B608`)
- [x] Safety — 0 vulnerabilidades en 63 paquetes
- [x] HTTP security headers — X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy, Content-Security-Policy
- [x] CSRF protection — flask-wtf, todas las rutas JSON exentas, logout usa POST con token

## Observabilidad

- [x] Logs estructurados con formato `key=value` — escritos a archivo y stdout
- [x] Promtail recoge logs del contenedor Docker automáticamente via stdout
- [x] cAdvisor provee métricas de contenedor (CPU, memoria, red)

## Producción

- [x] Dockerfile + docker-compose.yml con Gunicorn (-w 1 -b 0.0.0.0:8000)
- [x] Volúmenes para db/, static/uploads/ y logs/
- [x] Conectado a saas_network para integración con Nginx y stack de monitoreo
- [x] CI/CD con GitHub Actions — push a main despliega automáticamente al VPS
