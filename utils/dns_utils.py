import subprocess
import re
import dns.message
import dns.query
import dns.rdatatype
import dns.flags


def get_local_dns_ip():
    """Run scutil --dns and parse the first nameserver IP address from the output.
    
    Returns:
     IP address of the local DNS server
    """
    result = subprocess.run(["scutil", "--dns"], capture_output=True, text=True)
    match = re.search(r"nameserver\[0\]\s*:\s*([\d.]+)", result.stdout)
    if not match:
        raise RuntimeError("Could not find a nameserver IP in scutil --dns output")
    return match.group(1)


def query_cache(domain, dns_server_ip):
    """Send a non-recursive (RD=0) DNS query to check if a domain is in the resolver's cache.
    
    args:
     domain: the domain name to check,
     dns_server_ip:  IP address of the DNS server to query,
    Returns:
     tuple (is_cached, remaining_ttl). If not cached, remaining_ttl is None.
    """
    query = dns.message.make_query(domain, dns.rdatatype.A) # Create a DNS query object
    query.flags &= ~dns.flags.RD # Invert the RD flag to make the query non-recursive

    response = dns.query.udp(query, dns_server_ip, timeout=5) # Send the query to the DNS server

    for rrset in response.answer: # Iterate over the answer records
        if rrset.rdtype == dns.rdatatype.A: # If the record type is A (IPv4 address)
            return True, rrset.ttl # return the first A record's TTL

    return False, None
