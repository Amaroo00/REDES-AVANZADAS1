import json
import logging
import urllib3
import sys
import requests
from netmiko import ConnectHandler

# VERSION FINAL - CUMPLIMIENTO RÚBRICA
print("\n" + "="*50)
print(" AUTOMATIZACIÓN NETDEVOPS - EVALUACIÓN 1 ")
print("="*50 + "\n")

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- CREDENCIALES ---
CISCO_USER = 'cisco'; CISCO_PASS = 'cisco'
MIKROTIK_USER = 'admin'; MIKROTIK_PASS = 'juego12'

# --- NODOS (Gestión OOB) ---
R1 = {'device_type': 'cisco_ios', 'host': '192.168.122.10', 'username': CISCO_USER, 'password': CISCO_PASS, 'secret': CISCO_PASS}
R2 = {'device_type': 'cisco_ios', 'host': '192.168.122.20', 'username': CISCO_USER, 'password': CISCO_PASS, 'secret': CISCO_PASS}
R3_SSH = {'device_type': 'mikrotik_routeros', 'host': '192.168.122.30', 'username': MIKROTIK_USER, 'password': MIKROTIK_PASS}
R3_API = "http://192.168.122.30/rest" 
R3_AUTH = (MIKROTIK_USER, MIKROTIK_PASS)

def configurar_cisco():
    """Automatización Legacy via SSH para R1 y R2 (Pauta 3.4)"""
    logging.info(">>> INICIANDO AUTOMATIZACIÓN CISCO")
    try:
        # Configuración R2 (Router ISP)
        with ConnectHandler(**R2) as net:
            net.enable()
            logging.info("Configurando rutas estáticas base en R2 (ISP)...")
            net.send_config_set([
                "interface Gi0/1", "ip address 200.1.12.2 255.255.255.252", "no shut",
                "interface Gi0/2", "ip address 200.1.23.1 255.255.255.252", "no shut",
                "ip route 200.1.12.0 255.255.255.252 Gi0/1",
                "ip route 200.1.23.0 255.255.255.252 Gi0/2"
            ])
            
        # Configuración R1 (Sede Central)
        with ConnectHandler(**R1) as net:
            net.enable()
            logging.info("Configurando interfaces y VPN IPsec en R1...")
            config_commands = [
                "interface Gi0/1", "ip address 200.1.12.1 255.255.255.252", "no shut",
                "interface Lo10", "ip address 192.168.10.1 255.255.255.0",
                "ip route 0.0.0.0 0.0.0.0 200.1.12.2",
                "crypto isakmp policy 10",
                "encryption aes 128", "hash sha", "authentication pre-share", "group 2",
                "crypto isakmp key cisco1234 address 200.1.23.2",
                "crypto ipsec transform-set TS esp-aes esp-sha-hmac",
                "access-list 100 permit ip 192.168.10.0 0.0.0.255 192.168.30.0 0.0.0.255",
                "crypto map VPN 10 ipsec-isakmp",
                "set peer 200.1.23.2",
                "set transform-set TS",
                "match address 100",
                "interface Gi0/1", "crypto map VPN"
            ]
            net.send_config_set(config_commands)
            logging.info("Cisco R1 y R2 configurados exitosamente.")
    except Exception as e:
        logging.error(f"Error en automatización Cisco: {e}")

def configurar_r3_api():
    """Automatización Moderna via API REST para R3 (Pauta 3.5)"""
    logging.info(">>> INICIANDO AUTOMATIZACIÓN MIKROTIK (API REST)")
    try:
        # Preparación base vía SSH
        with ConnectHandler(**R3_SSH) as net:
            net.send_command("/ip service set www disabled=no port=80")
            net.send_command("/ip ipsec policy remove [find dst-address=192.168.10.0/24]")
            net.send_command("/ip ipsec peer remove [find name=peer1]")
            net.send_command("/ip address remove [find address=\"200.1.13.2/30\"]")
            # Configuración interfaces (ether2 es al ISP)
            net.send_command("/ip address add address=200.1.23.2/30 interface=ether2 disabled=no")
            net.send_command("/ip address add address=192.168.30.1/24 interface=bridge-vpn disabled=no")
            net.send_command("/ip route add gateway=200.1.23.1 disabled=no")

        # API
        requests.patch(f"{R3_API}/ip/ipsec/profile/*1", json={"hash-algorithm": "sha1", "enc-algorithm": "aes-128", "dh-group": "modp1024"}, auth=R3_AUTH)
        requests.patch(f"{R3_API}/ip/ipsec/proposal/*1", json={"auth-algorithms": "sha1", "enc-algorithms": "aes-128-cbc", "pfs-group": "none"}, auth=R3_AUTH)
        requests.put(f"{R3_API}/ip/ipsec/peer", json={"name": "peer1", "address": "200.1.12.1", "exchange-mode": "main", "profile": "default"}, auth=R3_AUTH)
        requests.put(f"{R3_API}/ip/ipsec/identity", json={"peer": "peer1", "auth-method": "pre-shared-key", "secret": "cisco1234"}, auth=R3_AUTH)

        payload = {
            "peer": "peer1", "src-address": "192.168.30.0/24", "dst-address": "192.168.10.0/24",
            "sa-src-address": "200.1.23.2", "sa-dst-address": "200.1.12.1", "tunnel": "yes", "action": "encrypt"
        }
        res = requests.put(f"{R3_API}/ip/ipsec/policy", json=payload, auth=R3_AUTH)
        
        # --- PARSEO JSON (Requisito 3.5 obligatorio) ---
        if res.status_code in [200, 201]:
            data = json.loads(res.text) # json.loads para demostrar parseo
            logging.info(f"ÉXITO: Política IPsec creada en MikroTik con ID: {data.get('.id')}")
        else:
            logging.error(f"Error en API REST: {res.text}")

    except Exception as e:
        logging.error(f"Error en automatización R3: {e}")

def verificar_r1():
    print("\n" + "=" * 50)
    print("VERIFICACIÓN R1 (Cisco)")
    print("=" * 50)
    try:
        with ConnectHandler(**R1) as net:
            net.enable()
            print("\n--- Hostname ---")
            print(net.send_command("show running-config | include hostname"))
            print("\n--- Interfaces IP ---")
            print(net.send_command("show ip interface brief"))
            print("\n--- Rutas ---")
            print(net.send_command("show ip route"))
            print("\n--- ISAKMP SA ---")
            print(net.send_command("show crypto isakmp sa"))
            print("\n--- IPSEC SA ---")
            print(net.send_command("show crypto ipsec sa"))
            print("\n--- Crypto Map ---")
            print(net.send_command("show crypto map"))
            print("\n--- Ping a R3 ---")
            res = net.send_command("ping 192.168.30.1 source 192.168.10.1 repeat 10")
            print(res)
            if "!!!" in res:
                print("\n" + "*"*45)
                print(" RESULTADO: VPN OPERATIVA (TRÁNSITO VIA ISP) ")
                print("*"*45)
    except Exception as e:
        print(f"Error verificando R1: {e}")

def verificar_r2():
    print("\n" + "=" * 50)
    print("VERIFICACIÓN R2 (Cisco)")
    print("=" * 50)
    try:
        with ConnectHandler(**R2) as net:
            net.enable()
            print("\n--- Interfaces IP ---")
            print(net.send_command("show ip interface brief"))
            print("\n--- Rutas ---")
            print(net.send_command("show ip route"))
    except Exception as e:
        print(f"Error verificando R2: {e}")

def verificar_r3():
    print("\n" + "=" * 50)
    print("VERIFICACIÓN R3 (MikroTik)")
    print("=" * 50)
    try:
        with ConnectHandler(**R3_SSH) as net:
            print("\n--- Sistema ---")
            print(f"Hostname: {net.send_command('/system identity print')}")
            print("\n--- Interfaces IP ---")
            print(net.send_command('/ip address print'))
            print("\n--- Rutas ---")
            print(net.send_command('/ip route print'))
            print("\n--- IPSec Peers ---")
            print(net.send_command('/ip ipsec peer print'))
            print("\n--- IPSec Policies ---")
            print(net.send_command('/ip ipsec policy print'))
    except Exception as e:
        print(f"Error verificando R3 via SSH: {e}")

def verificar():
    print("\n" + "=" * 60)
    print("VERIFICACIÓN COMPLETA DE LA RED VPN")
    print("=" * 60)
    verificar_r1()
    verificar_r2()
    verificar_r3()
    print("\n" + "=" * 60)
    print("VERIFICACIÓN FINALIZADA")
    print("=" * 60)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--verify":
        verificar()
    else:
        configurar_cisco()
        configurar_r3_api()
        print("\nAutomatización finalizada. Use --verify para validar.")
