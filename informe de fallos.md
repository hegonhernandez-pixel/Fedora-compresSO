Fedora compresSO — Informe técnico de fallos y malas implementaciones

Fecha: 9 de octubre de 2026
Tipo: Documento de transferencia entre agentes de trabajo
Alcance: Revisión preliminar basada en la configuración compartida del proyecto. No se dispone del repositorio completo, registros de compilación ni pruebas de arranque; por ello, los hallazgos se clasifican como riesgos pendientes de validación salvo que se indique lo contrario.
1. Registro de hallazgos
ID 	Hallazgo 	Prioridad provisional 	Estado
FCS-001 	Vulkan planteado como motor de arranque temprano 	Crítica arquitectónica 	Requiere aclarar su función
FCS-002 	Kernel 6.x-custom-vram sin versión exacta ni configuración reproducible 	Alta 	No verificado
FCS-003 	Dependencias del initramfs sin manifiesto explícito 	Alta 	No verificado
FCS-004 	Compresión sin algoritmo, nivel ni objetivos medibles 	Alta 	No especificado
FCS-005 	Sin estrategia documentada de recuperación del arranque 	Alta 	No verificado
FCS-006 	Compatibilidad de controladores gráficos no definida 	Alta 	No verificado
FCS-007 	Integración de escritorio incompleta en la configuración disponible 	Media 	Parcialmente documentado
FCS-008 	Sin matriz de pruebas, criterios de aceptación ni resultados 	Alta 	No aportados
2. Análisis técnico
FCS-001 — Vulkan en el arranque temprano

Reto: definir qué componente necesita Vulkan y en qué fase del arranque.

El kernel Linux utiliza el initramfs y un entorno de usuario temprano para localizar y montar el sistema raíz. Vulkan requiere una implementación compatible y dispositivos disponibles; no sustituye al mecanismo de arranque del kernel.

Correcciones propuestas

    Mantener el arranque inicial mediante kernel, initramfs y herramientas de espacio de usuario.
    Reservar Vulkan para una tarea concreta y demostrable, como procesamiento gráfico o compresión acelerada compatible.
    Establecer una ruta alternativa por CPU cuando la GPU o el controlador no estén disponibles.
    Medir si la aceleración reduce el tiempo total de arranque; no asumirlo.

Criterio de aceptación: el sistema arranca incluso sin Vulkan operativo.
FCS-002 — Kernel personalizado sin identificación reproducible

La etiqueta 6.x-custom-vram no identifica por sí sola una versión exacta, un commit, una configuración ni un conjunto de parches.

Correcciones propuestas

    Registrar versión base exacta, commit, parches y configuración del kernel.
    Identificar arquitectura, compilador y opciones relevantes de memoria y gráficos.
    Mantener un kernel Fedora de recuperación.
    Verificar módulos externos y su compatibilidad con el kernel generado.

Criterio de aceptación: las compilaciones son reproducibles y sus artefactos quedan identificados.
FCS-003 — Dependencias del initramfs

La lista disponible incluye mesa-vulkan-drivers, libdrm, vulkan-loader, vulkan-headers, zram-generator, btrfs-progs, xz, cpio y grub2-efi.

La lista no demuestra que el initramfs contenga todo lo necesario. Los encabezados de Vulkan son herramientas de desarrollo y no sustituyen al controlador ni al cargador en tiempo de ejecución. Las dependencias efectivas dependen del sistema raíz, el hardware y el método de generación del initramfs.

Correcciones propuestas

    Separar dependencias de compilación, instalación y arranque.
    Comprobar que el initramfs contiene los controladores de almacenamiento y sistema de archivos requeridos.
    Incluir componentes gráficos/Vulkan solo si se ejecutan realmente en esa fase.
    Inspeccionar el initramfs y probar el montaje del sistema raíz.

FCS-004 — Compresión sin especificación

La presencia de xz no demuestra que XZ sea el compresor configurado para el kernel o el initramfs.

Correcciones propuestas

    Especificar algoritmo, nivel, tamaño del artefacto y memoria máxima de descompresión.
    Medir tiempo de compresión, tiempo de arranque y consumo de RAM.
    Comparar la configuración propuesta con la configuración Fedora de referencia.
    Documentar qué se comprime: initramfs, sistema raíz, memoria RAM u otros artefactos.

Criterio de aceptación: mejora medible frente a la referencia sin comprometer la fiabilidad del arranque.
FCS-005 — Recuperación y seguridad del arranque

No se ha aportado evidencia de una entrada de recuperación, una política de firma o pruebas de actualización y reversión.

Correcciones propuestas

    Conservar una entrada de arranque funcional anterior.
    Validar kernel, initramfs y configuración del cargador antes de sustituir artefactos.
    Probar el arranque con módulos ausentes, errores de montaje y controladores gráficos no disponibles.
    Documentar la política de Secure Boot y firma de módulos, si se utiliza.
    Conservar registros de diagnóstico del initramfs.

FCS-006 — Compatibilidad gráfica

No se especifican GPU objetivo, controlador, versión de Mesa ni extensiones Vulkan necesarias.

Correcciones propuestas

    Definir el hardware objetivo.
    Validar detección de GPU, inicialización del controlador y creación de una instancia Vulkan.
    Probar equipos sin GPU compatible y sistemas con gráficos integrados.
    Evitar que un fallo gráfico impida montar el sistema raíz.

FCS-007 — Entorno de escritorio

La configuración disponible contiene únicamente el inicio del campo Default_Desktop = xf.... No permite confirmar qué escritorio se seleccionó ni si se instalaron sus componentes.

Correcciones propuestas

    Definir el escritorio y su versión.
    Registrar gestor de inicio de sesión, servidor gráfico o compositor y servicios necesarios.
    Verificar el inicio de sesión y la aceleración gráfica después de montar el sistema raíz.

FCS-008 — Ausencia de pruebas reproducibles

No se han aportado resultados de compilación, pruebas de hardware o mediciones de rendimiento.

Correcciones propuestas

    Crear una compilación automatizada.
    Ejecutar pruebas de arranque en máquina virtual y hardware objetivo.
    Registrar tiempos de arranque, tamaño del initramfs, consumo de RAM y errores.
    Bloquear la publicación cuando fallen las pruebas críticas.

3. Plan de trabajo priorizado
P0 — Asegurar el arranque

Responsable: agente de kernel/boot
Identificar la versión exacta, revisar el initramfs, comprobar dependencias y conservar una entrada de recuperación.
P1 — Validar Vulkan

Responsable: agente de gráficos
Definir la función de Vulkan en cada fase, verificar controladores y demostrar una ruta alternativa por CPU.
P2 — Medir la compresión

Responsable: agente de rendimiento
Comparar algoritmos, niveles de compresión, tamaños de artefactos y tiempos reales de arranque.
P3 — Automatizar la aceptación

Responsable: agente de integración
Crear pruebas repetibles, registrar resultados y generar un informe por compilación.
4. Paquete de transferencia a otros agentes
Objetivo

Auditar la arquitectura de arranque, el kernel personalizado, la integración Vulkan y la compresión. Corregir defectos demostrados sin introducir dependencias innecesarias.
Contexto conocido

    Base declarada: RedHat/Fedora minimal.
    Kernel declarado: 6.x-custom-vram.
    Arranque temprano declarado: Vulkan_Early_Boot.
    Componentes mencionados: Mesa Vulkan, libdrm, Vulkan Loader/Headers, zram-generator, btrfs-progs, xz, cpio y grub2-efi.
    Escritorio: configuración incompleta (xf...).

Hallazgos pendientes de validación

    FCS-001: papel de Vulkan en el arranque temprano.
    FCS-002: versión y configuración reproducibles del kernel.
    FCS-003: dependencias reales del initramfs.
    FCS-004: algoritmo y objetivos de compresión.
    FCS-005: recuperación y seguridad del arranque.
    FCS-006: compatibilidad GPU/controladores.
    FCS-007: configuración completa del escritorio.
    FCS-008: pruebas automatizadas y métricas.

Reglas de ejecución

    No declarar un defecto confirmado sin evidencia reproducible.
    No modificar el kernel o el arranque sin conservar una vía de recuperación.
    Separar dependencias de compilación y de ejecución.
    Medir las mejoras contra una referencia.
    Documentar versiones, commits, comandos y resultados.

Entregables obligatorios

    Informe de hallazgos con severidad, evidencia y pasos de reproducción.
    Parche o cambio mínimo propuesto.
    Resultado de compilación y pruebas.
    Riesgos residuales y método de reversión.
    Referencias a documentación oficial actual.

Condición de cierre

Cada hallazgo debe quedar como CONFIRMADO, DESCARTADO o BLOQUEADO POR FALTA DE EVIDENCIA. No marcar una corrección como terminada sin pruebas.
Restricción arquitectónica

Vulkan no debe considerarse sustituto del mecanismo de arranque del kernel ni requisito obligatorio para montar el sistema raíz. Su uso temprano debe justificarse con una necesidad medible y una ruta alternativa funcional.
5. Evidencia necesaria para completar la auditoría

Para convertir los riesgos identificados en fallos confirmados, recopilar:

    Repositorio o archivos de configuración de Fedora compresSO.
    Configuración .config del kernel y versión exacta del código fuente.
    Scripts de generación del initramfs y configuración de GRUB.
    Registro completo de compilación y, si existe, rdsosreport.txt.
    Hardware objetivo y mediciones actuales de compresión y arranque.

Conclusión

El principal reto arquitectónico es demostrar que Vulkan aporta una ventaja real sin convertirse en un punto único de fallo del arranque. La prioridad inmediata es asegurar un arranque reproducible y recuperable; después, medir y validar la compresión.
Referencias técnicas para verificar durante la auditoría

    Documentación oficial del kernel Linux sobre initramfs.
    Documentación oficial de dracut sobre generación y diagnóstico del initramfs.
    Documentación oficial de Vulkan Loader y Mesa.
    Documentación oficial de Fedora sobre kernel, GRUB y recuperación.
