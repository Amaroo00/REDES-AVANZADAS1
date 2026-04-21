# NetDevOps - Automatización Híbrida e IPsec

Este proyecto forma parte de la **Evaluación 01** de la asignatura **Redes Avanzadas I**. Consiste en la automatización de una red híbrida compuesta por equipos Cisco (IOSv) y MikroTik (CHR) utilizando **Python**, **Docker** y técnicas de **NetDevOps**.

## Requerimientos del Proyecto
- **Automatización Legacy:** Configuración de R1 y R2 (Cisco) mediante **SSH/Netmiko**.
- **Automatización Moderna:** Configuración de R3 (MikroTik) mediante **API REST (Requests/JSON)**.
- **Seguridad:** Establecimiento de un túnel VPN IPsec S2S entre R1 y R3.
- **Entorno:** Ejecución desde un contenedor Docker integrado en la red OOB de GNS3.

## Instrucciones de Ejecución

### 1. Preparación del Entorno
Asegúrate de tener GNS3 abierto y los routers encendidos. Desde la terminal en esta carpeta, construye y levanta el contenedor:

```bash
docker-compose up -d --build
```

### 2. Ejecutar Automatización
Para configurar toda la red Interfaces, Rutas y VPN, ejecuta:

```bash
docker exec -it <Iredes-vpn-1> python App.py
```

### 3. Verificar Conectividad
Para validar el estado de la VPN y realizar pruebas de ping LAN-to-LAN:

```bashAmaroo00/redes-avanzadas-ev1
docker exec -it <redes-vpn-1> python App.py --verify
```

## Tecnologías Utilizadas
- **Python 3.x**
- **Netmiko** 
- **Requests**
- **Docker & Docker Compose**
- **GNS3**

## Autores
- [Cristobal Figueroa, Dylan Palavecino, Bairon Chihuaicura]
- Asignatura: Redes Avanzadas I
- Sede: Inacap Temuco
