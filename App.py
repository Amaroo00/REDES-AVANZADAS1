import json
import logging
import urllib3
import sys
import requests
from netmiko import ConnectHandler

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- CREDENCIALES ---
CISCO_USER = 'cisco'; CISCO_PASS = 'cisco'
MIKROTIK_USER = 'admin'; MIKROTIK_PASS = 'juego12'

# --- NODOS ---
R1 = {'device_type': 'cisco_ios', 'host': '192.168.122.10', 'username': CISCO_USER, 'password': CISCO_PASS, 'secret': CISCO_PASS}
R2 = {'device_type': 'cisco_ios', 'host': '192.168.122.20', 'username': CISCO_USER, 'password': CISCO_PASS, 'secret': CISCO_PASS}
R3_SSH = {'device_type': 'mikrotik_routeros', 'host': '192.168.122.30', 'username': MIKROTIK_USER, 'password': MIKROTIK_PASS}
R3_API = "http://192.168.122.30/rest" # Usamos HTTP para evitar problemas de certificados
R3_AUTH = (MIKROTIK_USER, MIKROTIK_PASS)

def configurar_cisco():
    logging.info(">>> CONFIGURANDO CISCO (R1 y R2) VIA SSH")
    try:
        with ConnectHandler(**R2) as net:
            net.enable()
            net.send_config_set([
                "interface Gi0/1", "ip address 200.1.12.2 255.255.255.252", "no shut",
                "interface Gi0/2", "ip address 200.1.23.1 255.255.255.252", "no shut",
                "ip route 192.168.10.0 255.255.255.0 200.1.12.1",
                "ip route 192.168.30.0 255.255.255.0 200.1.23.2",
                "ip route 200.1.13.0 255.255.255.252 200.1.12.1"
            ])
        with ConnectHandler(**R1) as net:
            net.enable()
            net.send_config_set([
                "interface Gi0/1", "ip address 200.1.12.1 255.255.255.252", "no shut",
                "interface Gi0/2", "ip address 200.1.13.1 255.255.255.252", "no shut",
                "interface Lo10", "ip address 192.168.10.1 255.255.255.0",
                "ip route 0.0.0.0 0.0.0.0 200.1.12.2", "ip route 192.168.30.0 255.255.255.0 200.1.13.2",
                "crypto isakmp policy 10", "encryption aes 128", "hash sha", "authentication pre-share", "group 2",
                "crypto isakmp key cisco1234 address 0.0.0.0", "crypto isakmp identity address",
                "crypto ipsec transform-set TS esp-aes esp-sha-hmac",
                "access-list 100 permit ip 192.168.10.0 0.0.0.255 192.168.30.0 0.0.0.255",
                "crypto map VPN 10 ipsec-isakmp", "set peer 200.1.13.2", "set transform-set TS", "match address 100",
                "interface Gi0/2", "crypto map VPN"
            ])
            logging.info("Cisco R1 y R2 OK.")
    except Exception as e: logging.error(f"Error Cisco: {e}")

def configurar_r3_api():
    logging.info(">>> ACTIVANDO Y CONFIGURANDO MIKROTIK (R3) VIA API REST")
    try:
        # PRIMERO: Activar el servicio WWW vía SSH (Solo una vez)
        with ConnectHandler(**R3_SSH) as net:
            net.send_command("/ip service set www disabled=no port=80")
            logging.info("Servicio API REST (WWW) activado en R3.")

        # SEGUNDO: Configurar vía API REST (Requerimiento 3.5)
        # 1. Profile y Proposal
        requests.patch(f"{R3_API}/ip/ipsec/profile/*1", json={"hash-algorithm": "sha1", "enc-algorithm": "aes-128", "dh-group": "modp1024"}, auth=R3_AUTH)
        requests.patch(f"{R3_API}/ip/ipsec/proposal/*1", json={"auth-algorithms": "sha1", "enc-algorithms": "aes-128-cbc", "pfs-group": "none"}, auth=R3_AUTH)

        # 2. Peer e Identity
        requests.put(f"{R3_API}/ip/ipsec/peer", json={"name": "peer1", "address": "200.1.13.1", "exchange-mode": "main", "profile": "default"}, auth=R3_AUTH)
        requests.put(f"{R3_API}/ip/ipsec/identity", json={"peer": "peer1", "auth-method": "pre-shared-key", "secret": "cisco1234"}, auth=R3_AUTH)

        # 3. Policy y Ruta
        policy_payload = {
            "peer": "peer1", "src-address": "192.168.30.0/24", "dst-address": "192.168.10.0/24",
            "sa-src-address": "200.1.13.2", "sa-dst-address": "200.1.13.1", "tunnel": "yes", "action": "encrypt", "proposal": "default"
        }
        res = requests.put(f"{R3_API}/ip/ipsec/policy", json=policy_payload, auth=R3_AUTH)
        
        # Parseo JSON obligatorio (Pauta 3.5)
        if res.status_code in [200, 201]:
            data = json.loads(res.text)
            logging.info(f"Política IPSec creada vía API: {data}")

        requests.put(f"{R3_API}/ip/route", json={"dst-address": "192.168.10.0/24", "gateway": "200.1.13.1"}, auth=R3_AUTH)
        logging.info("R3 OK vía API REST.")
    except Exception as e: logging.error(f"Error API R3: {e}")

def verificar():
    logging.info(">>> VERIFICANDO CONECTIVIDAD FINAL")
    try:
        with ConnectHandler(**R1) as net:
            net.enable()
            res = net.send_command("ping 192.168.30.1 source 192.168.10.1")
            print(f"\nResultado Ping: {res}")
            if "!!!" in res: print(" ¡VPN FUNCIONANDO AL 100%!")
    except: pass

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--verify":
        verificar()
    else:
        configurar_cisco()
        configurar_r3_api()
        print("\nConfiguración terminada. Corre con --verify.")
