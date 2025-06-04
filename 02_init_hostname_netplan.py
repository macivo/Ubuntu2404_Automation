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
import time

def clean_write(netplan):
    # Writing to netplan-file
	with open("/etc/netplan/50-cloud-init.yaml", "w") as outfile:
		yaml.dump(netplan, outfile, default_style=None, default_flow_style=False, sort_keys=False)

    # Remove the apostrophes from yaml 
	with open("/etc/netplan/50-cloud-init.yaml", "rt") as filein:
		netplan = filein.read().replace("'", "")
	with open("/etc/netplan/50-cloud-init.yaml", "w") as outfile:
		outfile.write(netplan)
	# Apply netplan
	subprocess.run(["netplan", "apply"]) 

if __name__ == "__main__":

	# Getting inputs
	print("hostname?")
	hostname = str(input())
	print("ip?")
	ip = str(input())
	print("prefix?")
	prefix = str(input())

	# Init dictionary object
	netplan = {
		"network": {
			"version": 2,
			"renderer": "networkd",
			"ethernets": {}
		}
	}

	# set all interface dhcp
	interfaces = netifaces.interfaces()
	interfaces.remove("lo")
	for i in interfaces: netplan["network"]["ethernets"][i] = { "dhcp4": "yes" }
	clean_write(netplan)	
	
    # Define the fist ip-address as gateway
	ip_gateway = str(ipaddress.ip_network(ip+"/"+prefix, strict=False).network_address + 1)

    # Define the DNS IP address. In my case, we are running the edges in one of two networks
	ip_dns = "200.0.0.1" if ip.startswith("200.0.0") else "10.0.0.3"

	# Find a connected interface
	while True:
		found = False
		for i in interfaces:
			# Write values to the netplan
			if len(netifaces.ifaddresses(i)) > 1:
				netplan["network"]["ethernets"][i] = {}
				if_main = netplan["network"]["ethernets"][i]
				if_main["addresses"] = "["+ip+"/"+prefix +"]"
				if_main["routes"] = { "- to": "default", "  via": ip_gateway }
				if_main["nameservers"] = { "search": "[ DNS.local ]", "addresses": "[ "+ip_dns+" ]" }
				found = True
				break
		if found: break	
		print("No connected interface found. Waiting 5 secound to retry .....")
		time.sleep(5)

    # Apply the new hostname
	clean_write(netplan)
	subprocess.run(["hostnamectl", "set-hostname", hostname]) 
	subprocess.run(["reboot", "now"]) 