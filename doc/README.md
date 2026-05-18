# Sistema de Administración de Propiedades Comerciales

## Pendientes

- [ ] Recrear el diagrama del esquema SQL al final del proyecto
- [ ] Notificar a inquilino y arrendador cuando un documento esté por vencer
- [ ] Revisar el nombre y formato de los archivos subidos (actualmente UUID)
- [ ] Implementar notificaciones_log — registrar cada notificación enviada a inquilinos y arrendador
- [ ] Evaluar portal para inquilinos — permitir que inquilinos accedan a sus documentos, facturas y contrato desde la app (agregar rol inquilino a usuarios y asociarlo con inquilino_id)
- [ ] Implementar páginas de error HTML para 404 y 500 — actualmente devuelven JSON en navegador
- [ ] Agregar module docstring a todos los controllers — descripción general del módulo al inicio de cada archivo
- [ ] Verificar que acciones sensibles (crear usuario, desactivar usuario, eliminar registros) estén restringidas solo a roles admin y root — revisar en todas las rutas y en el frontend
- [x] Agregar manejo global de errores en src/__init__.py para errores inesperados de DB
- [x] Confirmar que el scheduler no requiere autenticación — llama a generate_invoice directamente sin pasar por una ruta
- [x] Bug lógico: usuario root podía ser desactivado por cualquier admin — se agregó guarda en `deactivate_user` que lanza `ValueError` si el rol es `root`
- [x] Bug: `area_m2` y `renta_base` en unidades aceptaban valores negativos — se agregó validación `> 0` en `create_unit` y `update_unit`
- [x] Bug: ruta PUT de unidades no atrapaba `ValueError` del controller — se agregó try/except en `modify_unit`
- [x] Bug: `dia_cobro` no tenía validación en el controller — se agregó validación `BETWEEN 1 AND 28` en `create_contract` y `update_contract`
- [x] Verificar try/except para `ValueError` en todas las rutas PUT/PATCH — `modify_tenant` faltaba try/except; `modify_maintenance` y `modify_document` ya lo tenían correcto
- [x] Actualizar todos los controllers para usar % formatting en lugar de f-strings en los logs
- [x] Renombrar parámetro `id` a nombre específico en todas las rutas y controllers
- [x] Agregar docstrings a todos los métodos de las rutas
- [x] Agregar module docstring a todos los controllers
- [x] Botón "+ Nuevo" cambia de texto al hacer click en todas las páginas — formulario se resetea al cancelar
- [x] Configurar SECRET_KEY como variable de entorno — app lanza RuntimeError si no está definida; se carga desde .env con python-dotenv

## Pruebas pendientes

- [ ] Unidades — crear, ver detalle, editar
  - [ ] Sugerencia: el campo `numero` no es intuitivo — evaluar reemplazarlo por un identificador con estructura definida (ej. `A-101`, `Local-03`) con validación de formato y unicidad
  - [ ] Pregunta de negocio: cambiar `estado` manualmente (ej. `ocupado` → `mantenimiento`) no está vinculado al contrato activo — definir si debe bloquearse, lanzar advertencia, o solo actualizar el estado sin tocar el contrato
- [ ] Inquilinos — crear, ver detalle, editar
  - [x] Bug: falta validación en `correo`, `telefono` y `rfc` — validación agregada en controller y frontend
  - [x] Bug lógico: el inquilino no expone un ID visible en la UI — se agregó campo ID en la vista de detalle
  - [ ] Bug: la BD tiene UNIQUE constraint en `correo` de inquilinos — debe eliminarse ya que un mismo inquilino puede rentar múltiples unidades
  - [x] UI: campos RFC y Creado se renderizan en dos líneas — corregido ajustando anchos de columna
- [ ] Contratos — crear (requiere unidad e inquilino), ver detalle, editar, terminar
  - [x] Bug: campos ID Unidad e ID Inquilino aceptaban entrada manual — reemplazados por selectores
  - [x] Bug: no se validaba que la unidad o el inquilino existan antes de crear el contrato — validación agregada en controller
  - [x] UI: las fechas `fecha_inicio` y `fecha_fin` se renderizan en dos líneas — corregido ampliando columnas a col-md-2
- [ ] Facturas — verificar generación automática por scheduler, registrar pago *(módulo aún no implementado — pendiente para después)*
- [ ] Mantenimientos — crear, actualizar estado, resolver
  - [x] Bug: `unidad_id` era campo de texto libre — reemplazado por selector con unidades existentes
  - [x] UI: colores agregados a `prioridad` — escala verde → azul → amarillo → rojo
  - [ ] Sugerencia: mostrar el contrato activo de la unidad dentro del detalle del mantenimiento
  - [x] Bug lógico: `descripcion` solo aceptaba una línea — implementado como journal acumulativo con fecha automática
  - [x] UI: selector de unidad se resetea al cancelar el formulario
- [ ] Documentos — subir archivo, verificar que se guarda correctamente
  - [x] Bug lógico: FKs eran opcionales y de texto libre — reemplazados por selectores; ahora los tres son requeridos
  - [ ] Pendiente: agregar alerta cuando un documento esté próximo a vencer
  - [ ] Bug lógico: no existe opción para eliminar un documento
- [ ] Usuarios — crear usuario staff, desactivar, reactivar
  - [ ] Pruebas de permisos pendientes por rol:
    - **Sin sesión:** acceder a cualquier ruta protegida debe devolver 401 (JSON) o redirigir a login (HTML)
    - **Staff:** puede ver unidades, inquilinos, contratos, facturas, mantenimientos — no debe poder crear usuarios, desactivar usuarios, eliminar unidades ni acceder a /usuarios/
    - **Admin:** puede hacer todo lo anterior más gestión de usuarios — no debe poder desactivar a root
    - **Root:** acceso total sin restricciones — verificar que no pueda ser desactivado por ningún otro rol
