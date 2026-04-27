# NetDevOps - Automatización Híbrida e IPsec

Este proyecto forma parte de la Evaluación 01 de la asignatura Redes Avanzadas I. Consiste en la automatización de una red híbrida compuesta por equipos Cisco (IOSv) y MikroTik (CHR) utilizando Python, Docker y técnicas de NetDevOps.

## Requerimientos del Proyecto
- **Automatización Legacy:** Configuración de R1 y R2 (Cisco) mediante **SSH/Netmiko**.
- **Automatización Moderna:** Configuración de R3 (MikroTik) mediante **API REST (Requests/JSON)**.
- **Seguridad:** Establecimiento de un túnel VPN IPsec S2S entre R1 y R3.
- **Entorno:** Ejecución desde un contenedor Docker integrado en la red OOB de GNS3.

## Instrucciones de Ejecución

### 1. Construcción de la Imagen Docker
Para asegurar que el contenedor utilice la versión correcta, construye la imagen localmente en la terminal de tu PC:

```bash
docker build -t app-redes-vpn:v3 .
```

### 2. Integración y Ejecución en GNS3
1. Agrega el nodo Docker (usando la imagen `app-redes-vpn:v3`) a tu topología en GNS3.
2. En la opción **Edit Config** del nodo, configúrale la IP estática `192.168.122.100`.
3. Inicia el nodo y abre su **Console**.

### 3. Ejecutar Automatización
Dentro de la consola del Docker en GNS3, ejecuta el script principal para configurar los routers:

```bash
python App.py
```

### 4. Verificar Conectividad
Para validar las tablas de ruteo, el estado de la VPN (Fase 1 y 2) y el ping cruzado, ejecuta en la misma consola:

```bash
python App.py --verify
```

## Tecnologías Utilizadas
- Python 3.14.3
- Netmiko
- Requests
- Docker & Docker Compose
- GNS3

## Integrante
- Cristobal Figueroa, Dylan Palavecino, Bairon Chihuaicura
- Asignatura: Redes Avanzadas I
- Sede: Inacap Temuco
