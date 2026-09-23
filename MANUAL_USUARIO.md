# WinGet GUI Manager Pro - Manual de Usuario

## 📖 **Tabla de Contenidos**

1. [Introducción](#introducción)
2. [Requisitos del Sistema](#requisitos-del-sistema)
3. [Instalación](#instalación)
4. [Interfaz Principal](#interfaz-principal)
5. [Funciones Básicas](#funciones-básicas)
6. [Funciones Avanzadas](#funciones-avanzadas)
7. [Control de Versiones](#control-de-versiones)
8. [Menú de Aplicación](#menú-de-aplicación)
9. [Atajos de Teclado](#atajos-de-teclado)
10. [Solución de Problemas](#solución-de-problemas)
11. [Contacto y Soporte](#contacto-y-soporte)

---

## 🚀 **Introducción**

**WinGet GUI Manager Pro** es una interfaz gráfica profesional para Windows Package Manager (WinGet) que facilita la gestión de paquetes y aplicaciones en Windows.

### **Características Principales:**
- ✅ Gestión completa de paquetes (instalar, actualizar, desinstalar)
- ✅ Búsqueda y filtrado avanzado
- ✅ Backup y restauración de configuración
- ✅ Gestión de fuentes de paquetes
- ✅ Control de versiones con historial
- ✅ Actualizaciones programadas
- ✅ Pin/Unpin de paquetes críticos
- ✅ Exportación en múltiples formatos

---

## 💻 **Requisitos del Sistema**

### **Mínimos:**
- Windows 10 (versión 1903) o superior
- Windows 11 (todas las versiones)
- WinGet CLI instalado
- 2 GB de RAM
- 100 MB de espacio libre

### **Recomendados:**
- Windows 11 (última versión)
- 4 GB de RAM o más
- Conexión a internet estable
- Permisos de administrador (recomendado)

---

## 📦 **Instalación**

### **Opción 1: Ejecutable Portable**
1. Descarga `WinGet_GUI_Manager_Pro.exe`
2. Colócalo en cualquier carpeta
3. Doble clic para ejecutar

### **Opción 2: Desde Código Fuente**
1. Asegúrate de tener Python 3.8+ y PySide6
2. Clona el repositorio
3. Ejecuta `pip install -r requirements.txt`
4. Ejecuta `python main.py`

### **Configuración Inicial:**
1. Ejecuta la aplicación
2. Verifica que WinGet está instalado
3. Espera a que se cargue la lista de paquetes

---

## 🎯 **Interfaz Principal**

### **Componentes Principales:**

```
┌─────────────────────────────────────────────────────────────┐
│ WinGet GUI Manager Pro - ☰ □ ✕                            │
├─────────────────────────────────────────────────────────────┤
│ Menú: Archivo | Editar | Ver | Herramientas | Ayuda        │
├─────────────────────────────────────────────────────────────┤
│ Paquetes Instalados                          Total: 34      │
├─────────────────────────────────────────────────────────────┤
│ Buscar: [               ] Fuente: [Todas ▼] ☐ Solo ↑  ☐ Sistema │
├─────────────────────────────────────────────────────────────┤
│ [Tabla de Paquetes con información completa]              │
├─────────────────────────────────────────────────────────────┤
│ [🔄Refrescar] [⬆️↑] [⚡Sel] [🚀Todo]                  │
│ [📦Instalar] [🗑️Desinst] [ℹ️Det] [💾Backup] [♻️Rest] [⚙️] │
├─────────────────────────────────────────────────────────────┤
│ Listo                                                    │
└─────────────────────────────────────────────────────────────┘
```

### **Columnas de la Tabla:**
- **Nombre:** Nombre completo del paquete
- **ID:** Identificador único del paquete
- **Versión Instalada:** Versión actual en el sistema
- **Versión Disponible:** Última versión disponible
- **Origen:** Fuente del paquete (winget, msstore, etc.)
- **Estado:** Actualizado, Actualizable o Pinned
- **Acciones:** Botón 📌 para pin/unpin

---

## 🔧 **Funciones Básicas**

### **1. Listar Paquetes**
- La aplicación carga automáticamente todos los paquetes instalados
- Usa el botón **🔄 Refrescar** para actualizar la lista
- El contador muestra paquetes visibles vs. totales

### **2. Buscar Paquetes**
- Escribe en el campo **Buscar** para filtrar por nombre o ID
- La búsqueda es en tiempo real
- Distingue entre mayúsculas y minúsculas

### **3. Filtrar Resultados**
- **Fuente:** Filtra por origen (winget, msstore, etc.)
- **Solo actualizables:** Muestra solo paquetes con actualizaciones
- **Incluir sistema:** Muestra/oculta paquetes del sistema

### **4. Actualizar Paquetes**
- **Individual:** Selecciona un paquete y haz clic en **⚡ Actualizar Sel.**
- **Masivo:** Usa **🚀 Actualizar Todo** para todos los actualizables
- **Bloquear:** Usa 📌 para pin un paquete y evitar actualizaciones

---

## 🚀 **Funciones Avanzadas**

### **1. Instalar Nuevos Paquetes**
1. Haz clic en **📦 Instalar Nuevo**
2. Ingresa el término de búsqueda
3. Selecciona la fuente si es necesario
4. Haz clic en **Instalar** junto al paquete deseado

### **2. Desinstalar Paquetes**
1. Selecciona el paquete en la tabla
2. Haz clic en **🗑️ Desinstalar**
3. Confirma la acción
4. Espera a que complete el proceso

### **3. Ver Detalles del Paquete**
1. Selecciona un paquete
2. Haz clic en **ℹ️ Detalles**
3. Revisa información completa:
   - Versión y fuentes
   - Historial de actualizaciones
   - Dependencias
   - Tamaño y descripción

### **4. Backup y Restauración**
**Crear Backup:**
- Haz clic en **💾 Backup**
- Guarda el archivo JSON generado
- Incluye toda tu configuración

**Restaurar Backup:**
- Haz clic en **♻️ Restaurar**
- Selecciona tu archivo de backup
- Elige los paquetes a restaurar

### **5. Gestión de Fuentes**
1. Ve a **⚙️ Opciones → 📚 Gestionar Fuentes**
2. Agrega fuentes personalizadas con nombre y URL
3. Elimina fuentes no deseadas
4. Verifica disponibilidad de paquetes

### **6. Exportación de Datos**
- **CSV:** Importar a Excel o analizar datos
- **JSON:** Procesamiento de datos y automatización
- **TXT:** Documentación y registros

---

## 📊 **Control de Versiones**

### **Historial de Versiones**
Cada paquete mantiene un registro completo de:
- Fecha de instalación
- Versiones anteriores
- Fechas de actualización
- Tipo de cambios (major, minor, patch)

### **Información de Actualizaciones**
Para cada actualización disponible:
- **Tipo de actualización:** Major, Minor o Patch
- **Días desde última actualización**
- **Historial reciente de versiones**
- **Impacto potencial del cambio**

### **Actualizaciones Programadas**
Configura actualizaciones automáticas:
1. **Frecuencia:** Diaria, Semanal o Mensual
2. **Hora específica:** Personalizable
3. **Opciones:**
   - Excluir paquetes del sistema
   - Notificación previa
   - Backup automático

---

## 📋 **Menú de Aplicación**

### **Archivo (Alt+F)**
- **Nuevo Backup (Ctrl+N):** Crea backup inmediato
- **Abrir Backup (Ctrl+O):** Restaura desde archivo
- **Exportar Lista (Ctrl+E):** Exporta paquetes actuales
- **Salir (Ctrl+Q):** Cierra la aplicación

### **Editar (Alt+E)**
- **Refrescar Paquetes (F5):** Actualiza lista
- **Buscar Actualizaciones (Ctrl+U):** Escanea actualizaciones
- **Seleccionar Todo (Ctrl+A):** Selecciona todos los items

### **Ver (Alt+V)**
- **Mostrar Paquetes del Sistema:** Alterna visibilidad
- **Configurar Filtros:** Personaliza filtros por defecto

### **Herramientas (Alt+T)**
- **Instalar Paquete (Ctrl+I):** Busca e instala nuevos
- **Gestionar Fuentes:** Administra repositorios
- **Limpiar Caché:** Libera espacio temporal

### **Ayuda (Alt+H)**
- **Manual de Usuario (F1):** Abre este manual
- **Buscar Actualizaciones de la App:** Verifica versiones
- **Acerca de:** Información del programa y autor

---

## ⌨️ **Atajos de Teclado**

| Acción | Atajo | Descripción |
|--------|--------|-------------|
| Nuevo Backup | Ctrl+N | Crea backup de paquetes |
| Abrir Backup | Ctrl+O | Restaura desde backup |
| Exportar Lista | Ctrl+E | Exporta paquetes actuales |
| Instalar Paquete | Ctrl+I | Busca e instala |
| Buscar Actualizaciones | Ctrl+U | Escanea actualizaciones |
| Seleccionar Todo | Ctrl+A | Selecciona todos |
| Refrescar | F5 | Actualiza lista |
| Manual de Usuario | F1 | Abre ayuda |
| Salir | Ctrl+Q | Cierra aplicación |

### **Consejos de Productividad:**
- Usa **Ctrl+F** para búsqueda rápida en la tabla
- **Doble clic** en un paquete para ver detalles
- **Click derecho** para menú contextual
- **Arrastrar** para ordenar columnas
- **Ctrl+Scroll** para zoom en la tabla

---

## 🔧 **Solución de Problemas**

### **Problemas Comunes**

#### **❌ "WinGet no encontrado"**
**Causa:** WinGet CLI no está instalado o no está en PATH
**Solución:**
1. Abre PowerShell como administrador
2. Ejecuta: `winget --version`
3. Si no está instalado, instala desde Microsoft Store o GitHub
4. Reinicia la aplicación

#### **❌ "Error de permisos"**
**Causa:** La aplicación necesita permisos de administrador
**Solución:**
1. Cierra la aplicación
2. Haz clic derecho → "Ejecutar como administrador"
3. Repite la operación

#### **❌ "No se puede desinstalar paquete"**
**Causa:** El paquete está en uso o es del sistema
**Solución:**
1. Cierra todas las instancias del programa
2. Verifica que no sea un paquete crítico
3. Usa Panel de Control como alternativa

#### **❌ "Error de conexión"**
**Causa:** Problemas de red o con las fuentes
**Solución:**
1. Verifica tu conexión a internet
2. Ejecuta: `winget source reset`
3. Limpia caché desde el menú de herramientas

#### **❌ "La aplicación no responde"**
**Causa:** Operación en curso o bloqueo
**Solución:**
1. Espera unos minutos (operaciones largas)
2. Revisa la barra de progreso
3. Reinicia la aplicación si es necesario

### **Mensajes de Error Comunes**

| Error | Significado | Solución |
|-------|-------------|-----------|
| No tienes permisos | Necesitas admin | Ejecuta como administrador |
| Paquete no encontrado | No existe en fuentes | Verifica nombre o fuente |
| Ya actualizado | No hay actualizaciones | Paquete está al día |
| Espacio insuficiente | No hay disco | Libera espacio en disco |
| Error de conexión | Problemas de red | Verifica internet |

---

## 📞 **Contacto y Soporte**

### **Autor: Diego A. Rábalo**
- **LinkedIn:** [linkedin.com/in/rabalo](https://linkedin.com/in/rabalo)
- **Email:** (disponible en LinkedIn)

### **Soporte Técnico**
- **Documentación:** Manual integrado (F1)
- **Comunidad:** GitHub Issues
- **Actualizaciones:** Verificar en "Ayuda → Buscar Actualizaciones"

### **Reportar Problemas**
Para reportar errores, incluye:
1. **Versión de Windows**
2. **Versión de la aplicación**
3. **Pasos para reproducir**
4. **Mensaje de error completo**
5. **Logs de la aplicación**

### **Sugerencias y Mejoras**
¡Tus sugerencias son bienvenidas!
- Funcionalidades deseadas
- Mejoras en la interfaz
- Optimización de rendimiento
- Nuevas fuentes de paquetes

---

## 📄 **Licencia**

**WinGet GUI Manager Pro** está licenciado bajo MIT License.

Copyright © 2025 Diego A. Rábalo - Todos los derechos reservados.

---

## 🔄 **Historial de Versiones**

### **v2.0 Pro (Actual)**
- ✅ Barra de menú completa
- ✅ Control de versiones avanzado
- ✅ Actualizaciones programadas
- ✅ Manual de usuario integrado
- ✅ Mejor manejo de errores
- ✅ Historial de paquetes

### **v1.0**
- ✅ Funcionalidad básica
- ✅ Instalación/Desinstalación
- ✅ Backup y Restauración
- ✅ Exportación básica

---

**Gracias por usar WinGet GUI Manager Pro!** 🎉

Esta aplicación fue desarrollada para facilitar la gestión de paquetes Windows y mejorar tu productividad.