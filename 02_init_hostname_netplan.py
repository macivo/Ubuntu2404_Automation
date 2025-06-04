######################################################################################################
# This Python file creates a Netplan file with a static ip-address and set th new hostname
# @author Mac Müller 
# Date: 03.June.2025
# https://www.linkedin.com/in/mac-mueller/
# https://github.com/macivo/
######################################################################################################

import netifaces
import ipaddress
import yaml
import subprocess

# Find the first interface to set as static-adrdress
def get_active_interface():
	for interface in netifaces.interfaces():
		if netifaces.ifaddresses(interface) and interface != "lo":
			return interface
	return None

if __name__ == "__main__":
	# Getting inputs
	print("hostname?")
	hostname = str(input())
	print("ip?")
	ip = str(input())
	print("prefix?")
	prefix = str(input())
	
    # Define the fist ip-address as gateway
	ip_gateway = str(ipaddress.ip_network(ip+"/"+prefix, strict=False).network_address + 1)

    # Define the DNS IP address. In my case, we are running the edges in one of two networks
	ip_dns = "200.0.0.1" if ip.startswith("200.0.0") else "10.0.0.3"
	
    # Init dictionary object
	netplan = {
		"network": {
			"version": 2,
			"renderer": "networkd",
			"ethernets": {}
		}
	}
    # Write values to the netplan
	netplan["network"]["ethernets"][get_active_interface()] = {}
	if_main = netplan["network"]["ethernets"][get_active_interface()]
	if_main["addresses"] = "["+ip+"/"+prefix +"]"
	if_main["routes"] = { "- to": "default", "  via": ip_gateway }
	if_main["nameservers"] = { "search": "[ DNS.local ]", "addresses": "[ "+ip_dns+" ]" }
	
    # Writing to netplan-file
	with open("/etc/netplan/50-cloud-init.yaml", "w") as outfile:
		yaml.dump(netplan, outfile, default_style=None, default_flow_style=False, sort_keys=False)

    # Remove the apostrophes from yaml 
	with open("/etc/netplan/50-cloud-init.yaml", "rt") as filein:
		netplan = filein.read().replace("'", "")
	with open("/etc/netplan/50-cloud-init.yaml", "w") as outfile:
		outfile.write(netplan)	

    # Apply netplan to the system and change the hostname
	subprocess.run(["hostnamectl", "set-hostname", hostname]) 
	subprocess.run(["netplan", "apply"]) 
