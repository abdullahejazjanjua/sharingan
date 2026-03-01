import time
import random

from colorama import Fore, Style

from .config import MIN_DELAY, MAX_DELAY
from .dns_utils import query_cache


def analyze_websites(websites, dns_server_ip):
    """Check each website for DNS cache presence with random delays between checks.

    websites -- list of domain name strings to check
    dns_server_ip -- IP address of the DNS server to query
    """
    results = []
    for i, domain in enumerate(websites):
        if i > 0:
            delay = random.uniform(MIN_DELAY, MAX_DELAY)
            print(f"  {Fore.GREEN}[DELAY]{Style.RESET_ALL} {delay:.1f}s before next probe...")
            time.sleep(delay)

        cached, remaining_ttl = query_cache(domain, dns_server_ip)

        if cached:
            print(
                f"  {Fore.GREEN}[SCANNING]{Style.RESET_ALL} {domain:<25} "
                f"{Fore.GREEN}FOUND{Style.RESET_ALL}  "
                f"{Fore.CYAN}[TTL: {remaining_ttl}s]{Style.RESET_ALL}"
            )
        else:
            print(
                f"  {Fore.GREEN}[SCANNING]{Style.RESET_ALL} {domain:<25} "
                f"{Fore.RED}NOT FOUND{Style.RESET_ALL}"
            )

        results.append({
            "domain": domain,
            "cached": cached,
            "remaining_ttl": remaining_ttl,
        })

    return results
