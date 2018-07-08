import socket
import sys
from ipwhois import IPWhois
import ipaddress
import os
import subprocess
import concurrent.futures
from termcolor import colored
MAX_WORKERS = 100

################### Warnings: Plz shut the **** up #################
import warnings
warnings.filterwarnings("ignore")
###################################################################

def get_ip(domain):
	ip_address = None

	try:
		ip_address = socket.gethostbyname(domain)
	except Exception as e:
		logging.info("Unable to get ip address for host:{}".format(domain))

	return ip_address

def get_ip_list(ip):
	
	ip_list = []
	resp = IPWhois(ip).lookup_whois()
	if not resp:
		return ip_list
	network_address = resp.get("nets",{})
	if not network_address:
		return ip_list
	ip_range_string = network_address[0]["range"]
	if not ip_range_string:
		return ip_list
	ip_list = ip_range_string.split("-")
	
	return ip_list

FNULL = open(os.devnull, 'w')


def ping_ip(ip):
	is_up = False
	try:
		subprocess.check_call(['ping', '-c', '1', str(ip)], stdout=FNULL,stderr=FNULL)
	except Exception as e:
		print(colored(("[-] {} Down".format(ip)), 'red'))
		return (ip,is_up)
	else:
		# print()
		print(colored(("[+] {} Up".format(ip)), 'green'))
	is_up = True
	return (ip,is_up)

def all_ips_for_range(ip_list):
	count = 0
	starting = ip_list[0].strip()
	ending_ip = ip_list[1].strip()
	all_up_ips = []
	ip_list = [ipaddr for ipaddr in ipaddress.summarize_address_range(ipaddress.IPv4Address(starting),ipaddress.IPv4Address(ending_ip))]
	if not ip_list:
		print("Unable to get ip range")
		return all_up_ips

	with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
		future_to_url = {executor.submit(ping_ip,ip): ip for ip in ip_list[0]}
		for future in concurrent.futures.as_completed(future_to_url):
			ip = future_to_url[future]
			try:
				data = future.result()
			except Exception as exc:
				pass
			else:
				if data[1]:
					all_up_ips.append(str(data[0]))

	return all_up_ips

def get_network_range_for_domain(domain):

	if not domain:
		print("Plz provide domain inorder to get the network range")
		return {}
	ip_address = get_ip(domain)
	
	if not ip_address:
		print("Unable to resolve domain")
		return {}		
	
	ip_list = get_ip_list(ip_address)
	if not ip_list:
		print ("Unable to extract Network range")
		return {}
	return ip_list

def get_all_up_ips(domain):

	ip_list = get_network_range_for_domain(domain)
	if not ip_list:
		return 
	all_ips = all_ips_for_range(ip_list)
	if not all_ips:
		print("All IP are down for {}".format(domain))
	print("Total IPs Up")
	print (all_ips)

def main():
	domain = sys.argv[1]
	get_all_up_ips(domain)

if __name__ == '__main__':
	main()
