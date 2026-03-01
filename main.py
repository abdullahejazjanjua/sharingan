import json
import argparse

from colorama import init, Fore, Style

from utils.config import DUMMY_DNS_IP, DEFAULT_WEBSITES_PATH, BANNER, BAR_WIDTH
from utils.dns_utils import get_local_dns_ip
from utils.cache_analyzer import analyze_websites


def display_results(results):
    """Print a ranked, color-coded summary of DNS cache check results.

    results -- list of dicts, each with keys: domain, cached, remaining_ttl
    """
    cached = sorted(
        [r for r in results if r["cached"]],
        key=lambda r: r["remaining_ttl"],
    )
    not_cached = [r for r in results if not r["cached"]]

    border = f"{Fore.GREEN}{'═' * 60}{Style.RESET_ALL}"
    dim_border = f"{Fore.GREEN}{'─' * 60}{Style.RESET_ALL}"

    print(f"\n  {border}")
    print(f"  {Fore.GREEN} POPULARITY RANKING{Style.RESET_ALL}")
    print(f"  {border}\n")

    if cached:
        max_ttl = max(r["remaining_ttl"] for r in cached)

        for rank, r in enumerate(cached, 1):
            ttl = r["remaining_ttl"]
            if max_ttl > 0:
                filled = BAR_WIDTH - int((ttl / max_ttl) * BAR_WIDTH)
            else:
                filled = BAR_WIDTH
            bar = "█" * filled + "░" * (BAR_WIDTH - filled)

            rank_str = f"{Fore.YELLOW}#{rank:<3}{Style.RESET_ALL}"
            domain_str = f"{Fore.GREEN}{r['domain']:<22}{Style.RESET_ALL}"
            bar_str = f"{Fore.GREEN}[{bar}]{Style.RESET_ALL}"
            ttl_str = f"{Fore.CYAN}TTL: {ttl}s{Style.RESET_ALL}"

            print(f"  {rank_str} {domain_str} {bar_str}  {ttl_str}")

    if not_cached:
        print(f"\n  {dim_border}")
        print(f"  {Fore.RED} NOT IN CACHE{Style.RESET_ALL}")
        print(f"  {dim_border}\n")

        for r in not_cached:
            print(f"       {Fore.RED}{r['domain']}{Style.RESET_ALL}")

    total = len(results)
    found = len(cached)
    print(f"\n  {border}")
    print(
        f"  {Fore.GREEN} {found}{Style.RESET_ALL} of "
        f"{Fore.CYAN}{total}{Style.RESET_ALL} domains found in cache"
    )
    print(f"  {border}\n")


def main():
    """Orchestrate the DNS cache checking process."""
    init()

    parser = argparse.ArgumentParser(description="DNS Cache Checker")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Use a dummy DNS IP (8.8.8.8) instead of the local resolver",
    )
    parser.add_argument(
        "--nums",
        type=int,
        default=None,
        help="Number of websites to check from the JSON file",
    )
    args = parser.parse_args()

    print(f"{Fore.GREEN}{BANNER}{Style.RESET_ALL}")

    with open(DEFAULT_WEBSITES_PATH, "r") as f:
        websites = json.load(f)["websites"]

    if args.nums is not None:
        websites = websites[:args.nums]

    if args.test:
        dns_ip = DUMMY_DNS_IP
        mode = "TEST"
    else:
        dns_ip = get_local_dns_ip()
        mode = "LIVE"

    print(
        f"  {Fore.CYAN}Target DNS :{Style.RESET_ALL} {Fore.GREEN}{dns_ip}{Style.RESET_ALL}    "
        f"{Fore.CYAN}Domains :{Style.RESET_ALL} {Fore.GREEN}{len(websites)}{Style.RESET_ALL}    "
        f"{Fore.CYAN}Mode :{Style.RESET_ALL} {Fore.YELLOW}{mode}{Style.RESET_ALL}\n"
    )

    results = analyze_websites(websites, dns_ip)

    display_results(results)


if __name__ == "__main__":
    main()
