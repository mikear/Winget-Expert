# WinGet Expert - Manual de Usuario

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

**WinGet Expert** es una interfaz gráfica profesional para Windows Package Manager (WinGet) que facilita la gestión de paquetes y aplicaciones en Windows.

### **Características Principales:**
- ✅ Gestión completa de paquetes (instalar, actualizar, desinstalar)
- ✅ Búsqueda y filtrado avanzado
- ✅ Copias de seguridad y restauración
- ✅ Gestión de fuentes de paquetes
- ✅ Historial de acciones por paquete
- ✅ Pines reales de WinGet (bloquear actualizaciones)
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

### **Opción 1: Instalador (recomendado)**
1. Descarga `WinGet_Expert_Instalador.exe`
2. Doble clic y sigue el asistente (en español)
3. Crea accesos directos y entrada en "Aplicaciones instaladas"

### **Opción 2: Ejecutable Portable**
1. Descarga `WinGet_Expert.exe`
2. Colócalo en cualquier carpeta
3. Doble clic para ejecutar (sin instalación)

### **Opción 3: Desde Código Fuente**
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
│ WinGet Expert - ☰ □ ✕                                      │
├─────────────────────────────────────────────────────────────┤
│ Menú: Archivo | Editar | Ver | Herramientas | Ayuda        │
├─────────────────────────────────────────────────────────────┤
│ [Refrescar] [Actualizaciones] | [Instalar] [Detalles]      │
│ [Desinstalar] [Actualizar Sel.] [Actualizar Todo]          │
│ [Copia seg.] [Restaurar] [Exportar] | [Opciones]           │
├─────────────────────────────────────────────────────────────┤
│ Paquetes Instalados                          Total: 34      │
├─────────────────────────────────────────────────────────────┤
│ Buscar: [               ] Fuente: [Todas ▼] ☐ Solo ↑  ☐ Sistema │
│ Vista: [Tabla ▼] Agrupar: [Fuente ▼]              ☐ Silencioso │
├─────────────────────────────────────────────────────────────┤
│ [Tabla de Paquetes con información completa]              │
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
- **Estado:** Actualizado, Actualizable o Fijado
- **Acciones:** Menú contextual (clic derecho) para fijar/copiar ID

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
- **Individual:** Selecciona un paquete y haz clic en **Actualizar Sel.**
- **Masivo:** Usa **Actualizar Todo** para todos los actualizables
- **Bloquear:** Usa **Fijar** (clic derecho) para que un paquete no se actualice

---

## 🚀 **Funciones Avanzadas**

### **1. Instalar Nuevos Paquetes**
1. Haz clic en **Instalar**
2. Ingresa el término de búsqueda
3. Haz clic en **Instalar** junto al paquete deseado

### **2. Desinstalar Paquetes**
1. Selecciona el paquete en la tabla
2. Haz clic en **Desinstalar**
3. Confirma la acción
4. Sigue el log en vivo hasta que complete

### **3. Ver Detalles del Paquete**
1. Haz doble clic en un paquete (o botón **Detalles**)
2. Revisa información completa:
   - Versión y fuentes
   - Historial de acciones
   - Descripción y datos del catálogo

### **4. Copias de Seguridad y Restauración**
**Crear copia de seguridad:**
- Haz clic en **Copia seg.**
- Guarda el archivo JSON generado
- Incluye todos tus paquetes instalados

**Restaurar copia de seguridad:**
- Haz clic en **Restaurar**
- Selecciona tu archivo de copia de seguridad
- Elige los paquetes a restaurar

### **5. Gestión de Fuentes**
1. Ve a **Opciones → Gestionar Fuentes**
2. Agrega fuentes personalizadas con nombre y URL
3. Elimina fuentes no deseadas

### **6. Exportación de Datos**
- **CSV:** Importar a Excel o analizar datos
- **JSON:** Procesamiento de datos y automatización
- **TXT:** Documentación y registros

---

## 📊 **Historial de Acciones**

### **Registro por Paquete**
Cada paquete mantiene un historial de las acciones hechas desde la aplicación:
- Fecha de instalación (registro de Windows)
- Instalaciones y actualizaciones (con versión)
- Desinstalaciones

### **Dónde Verlo**
- Doble clic en un paquete → pestaña **Historial**
- Columnas **Instalado** y **Actualizado** de la tabla

---

## 📋 **Menú de Aplicación**

### **Archivo (Alt+F)**
- **Nueva copia de seguridad (Ctrl+N):** Crea copia inmediata
- **Abrir copia de seguridad (Ctrl+O):** Restaura desde archivo
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
- **Acerca de...:** Información del programa y autor

---

## ⌨️ **Atajos de Teclado**

| Acción | Atajo | Descripción |
|--------|--------|-------------|
| Nueva copia de seguridad | Ctrl+N | Crea copia de paquetes |
| Abrir copia de seguridad | Ctrl+O | Restaura desde copia |
| Exportar Lista | Ctrl+E | Exporta paquetes actuales |
| Instalar Paquete | Ctrl+I | Busca e instala |
| Buscar Actualizaciones | Ctrl+U | Escanea actualizaciones |
| Buscar en la lista | Ctrl+F | Enfoca el buscador |
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

**WinGet Expert** está licenciado bajo MIT License.

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
- ✅ Copias de seguridad y restauración
- ✅ Exportación básica

---

**Gracias por usar WinGet Expert!** 🎉

Esta aplicación fue desarrollada para facilitar la gestión de paquetes Windows y mejorar tu productividad.