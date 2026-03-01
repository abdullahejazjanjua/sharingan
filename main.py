import json
import time
import argparse

from colorama import init, Fore, Style

from utils.config import (
    DUMMY_DNS_IP, DEFAULT_WEBSITES_PATH, BANNER, BAR_WIDTH,
    DEFAULT_ROUNDS, SNAPSHOT_DELAY,
)
from utils.dns_utils import get_local_dns_ip
from utils.cache_analyzer import analyze_websites


def aggregate_results(all_rounds, websites):
    """Count how many rounds each domain was found in the cache.
    
    args:
     all_rounds: list of lists, each inner list is a round's results from analyze_websites,
     websites: full list of domain strings checked
    returns:
     dict mapping domain to found_count across rounds
    """
    counts = {domain: 0 for domain in websites}

    for round_results in all_rounds:
        for r in round_results:
            if r["cached"]:
                counts[r["domain"]] += 1

    return counts


def display_results(counts, total_rounds):
    """Print a frequency-ranked, color-coded summary of DNS cache check results.

    args:
     counts: dict mapping domain to found_count across rounds,
     total_rounds: number of snapshot rounds taken
    """
    found = sorted(
        [(domain, count) for domain, count in counts.items() if count > 0],
        key=lambda x: x[1],
        reverse=True,
    )
    not_found = [domain for domain, count in counts.items() if count == 0]

    border = f"{Fore.GREEN}{'═' * 60}{Style.RESET_ALL}"
    dim_border = f"{Fore.GREEN}{'─' * 60}{Style.RESET_ALL}"

    print(f"\n  {border}")
    print(f"  {Fore.GREEN} POPULARITY RANKING{Style.RESET_ALL}")
    print(f"  {border}\n")

    if found:
        for rank, (domain, count) in enumerate(found, 1):
            filled = int((count / total_rounds) * BAR_WIDTH)
            bar = "█" * filled + "░" * (BAR_WIDTH - filled)

            rank_str = f"{Fore.YELLOW}#{rank:<3}{Style.RESET_ALL}"
            domain_str = f"{Fore.GREEN}{domain:<22}{Style.RESET_ALL}"
            bar_str = f"{Fore.GREEN}[{bar}]{Style.RESET_ALL}"
            freq_str = f"{Fore.CYAN}{count}/{total_rounds} rounds{Style.RESET_ALL}"

            print(f"  {rank_str} {domain_str} {bar_str}  {freq_str}")

    if not_found:
        print(f"\n  {dim_border}")
        print(f"  {Fore.RED} NOT IN CACHE{Style.RESET_ALL}")
        print(f"  {dim_border}\n")

        for domain in not_found:
            print(f"       {Fore.RED}{domain}{Style.RESET_ALL}")

    print(f"\n  {border}")
    print(
        f"  {Fore.GREEN} {len(found)}{Style.RESET_ALL} of "
        f"{Fore.CYAN}{len(counts)}{Style.RESET_ALL} domains seen in cache "
        f"across {Fore.YELLOW}{total_rounds}{Style.RESET_ALL} round(s)"
    )
    print(f"  {border}\n")


def main():
    """Orchestrate the DNS cache checking process."""
    init()

    parser = argparse.ArgumentParser(description="Sharingan - DNS Cache Checker")
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
    parser.add_argument(
        "--rounds",
        type=int,
        default=DEFAULT_ROUNDS,
        help=f"Number of snapshot rounds (default: {DEFAULT_ROUNDS})",
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
        f"{Fore.CYAN}Mode :{Style.RESET_ALL} {Fore.YELLOW}{mode}{Style.RESET_ALL}    "
        f"{Fore.CYAN}Rounds :{Style.RESET_ALL} {Fore.YELLOW}{args.rounds}{Style.RESET_ALL}\n"
    )

    all_rounds = []
    for i in range(args.rounds):
        print(
            f"  {Fore.YELLOW}══ Round {i + 1}/{args.rounds} "
            f"{'═' * 44}{Style.RESET_ALL}\n"
        )

        results = analyze_websites(websites, dns_ip)
        all_rounds.append(results)

        if i < args.rounds - 1:
            remaining = SNAPSHOT_DELAY
            while remaining > 0:
                mins, secs = divmod(remaining, 60)
                print(
                    f"\r  {Fore.CYAN}[WAITING]{Style.RESET_ALL} "
                    f"Next round in {Fore.YELLOW}{mins:02d}:{secs:02d}{Style.RESET_ALL}  ",
                    end="", flush=True,
                )
                time.sleep(1)
                remaining -= 1
            print()

    counts = aggregate_results(all_rounds, websites)
    display_results(counts, args.rounds)


if __name__ == "__main__":
    main()
