
import subprocess
import time
import re
import statistics
from datetime import datetime

# ============================================================
# CONFIGURATION
# ============================================================

WIFI_INTERFACE = "YOUR_WIFI_INTERFACE"

WIFI_NETWORKS = [
    "YOUR_WIFI_NETWORK_1",
    "YOUR_WIFI_NETWORK_2",
]

CHECK_INTERVAL = 60          # seconds
PING_HOST = "1.1.1.1"
PING_COUNT = 5

# Don't switch just because of one bad check.
BAD_CHECKS_BEFORE_SWITCH = 2

# After switching, give Wi-Fi time to stabilize.
SWITCH_WAIT = 12

# Don't immediately switch back and forth.
COOLDOWN_AFTER_SWITCH = 90


# ============================================================
# TERMINAL HELPERS
# ============================================================

def run_command(command, timeout=15):
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()

    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"

    except Exception as e:
        return -1, "", str(e)


# ============================================================
# CURRENT WIFI
# ============================================================

def get_current_wifi():
    """
    Returns the currently connected SSID on en0.
    """

    code, stdout, stderr = run_command([
        "networksetup",
        "-getairportnetwork",
        WIFI_INTERFACE
    ])

    match = re.search(
        r"Current (?:Wi-Fi|AirPort) Network:\s*(.+)",
        stdout
    )

    if match:
        return match.group(1).strip()

    return None


# ============================================================
# INTERNET TEST
# ============================================================

def ping_test():
    """
    Returns:
        packet_loss_percent
        average_latency_ms
    """

    code, stdout, stderr = run_command([
        "ping",
        "-c",
        str(PING_COUNT),
        "-W",
        "1000",
        PING_HOST
    ], timeout=15)

    if code != 0:
        return 100.0, None

    # Example:
    # 5 packets transmitted, 5 packets received, 0.0% packet loss

    loss_match = re.search(
        r"([\d.]+)% packet loss",
        stdout
    )

    packet_loss = (
        float(loss_match.group(1))
        if loss_match
        else 100.0
    )

    # Example:
    # round-trip min/avg/max/stddev = 8.123/10.234/12.345/1.234 ms

    latency_match = re.search(
        r"=\s*[\d.]+/([\d.]+)/",
        stdout
    )

    average_latency = (
        float(latency_match.group(1))
        if latency_match
        else None
    )

    return packet_loss, average_latency


# ============================================================
# SCORE CALCULATION
# ============================================================

def calculate_score(packet_loss, latency):
    """
    Score is 0-100.

    Higher = better.

    Scoring:

        Internet reachable       -> major factor
        Packet loss              -> major factor
        Latency                  -> secondary factor
    """

    # Completely unreachable
    if latency is None or packet_loss >= 100:
        return 0

    # --------------------------------------------------------
    # Packet-loss score
    # --------------------------------------------------------

    # 0% loss  -> 100
    # 50% loss -> 0
    loss_score = max(
        0,
        100 - (packet_loss * 2)
    )

    # --------------------------------------------------------
    # Latency score
    # --------------------------------------------------------

    if latency <= 20:
        latency_score = 100

    elif latency <= 50:
        latency_score = 90

    elif latency <= 100:
        latency_score = 75

    elif latency <= 200:
        latency_score = 50

    elif latency <= 400:
        latency_score = 25

    else:
        latency_score = 0

    # --------------------------------------------------------
    # Final score
    # --------------------------------------------------------

    score = (
        loss_score * 0.65 +
        latency_score * 0.35
    )

    return round(score, 1)


# ============================================================
# CHECK A NETWORK
# ============================================================

def check_current_network():
    ssid = get_current_wifi()

    if not ssid:
        return {
            "ssid": None,
            "loss": 100,
            "latency": None,
            "score": 0
        }

    loss, latency = ping_test()

    score = calculate_score(
        loss,
        latency
    )

    return {
        "ssid": ssid,
        "loss": loss,
        "latency": latency,
        "score": score
    }


# ============================================================
# SWITCH WIFI
# ============================================================

def switch_wifi(ssid):
    print(f"\n>>> Switching to: {ssid}")

    # IMPORTANT:
    # We intentionally don't treat networksetup's return code
    # as the final truth. macOS can report an error while the
    # connection transition is still occurring.

    code, stdout, stderr = run_command([
        "networksetup",
        "-setairportnetwork",
        WIFI_INTERFACE,
        ssid
    ], timeout=20)

    if stdout:
        print(f"networksetup: {stdout}")

    if stderr:
        print(f"networksetup stderr: {stderr}")

    print(f">>> Waiting {SWITCH_WAIT}s for Wi-Fi to stabilize...")

    time.sleep(SWITCH_WAIT)

    actual_wifi = get_current_wifi()

    if actual_wifi == ssid:
        print(f">>> Successfully connected to {ssid}")
        return True

    print(f">>> Switch verification failed.")
    print(f">>> Current Wi-Fi: {actual_wifi}")

    return False


# ============================================================
# LOGGING
# ============================================================

def log_status(result):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    ssid = result["ssid"]
    latency = result["latency"]
    loss = result["loss"]
    score = result["score"]

    latency_text = (
        f"{latency:.1f} ms"
        if latency is not None
        else "N/A"
    )

    print(
        f"[{now}] "
        f"Wi-Fi={ssid} | "
        f"Latency={latency_text} | "
        f"Loss={loss:.1f}% | "
        f"Score={score}/100"
    )


# ============================================================
# MAIN MONITOR
# ============================================================

def main():

    print("=" * 60)
    print("Wi-Fi Auto Switcher")
    print("=" * 60)
    print(f"Interface : {WIFI_INTERFACE}")
    print(f"Networks  : {', '.join(WIFI_NETWORKS)}")
    print(f"Interval  : {CHECK_INTERVAL}s")
    print("=" * 60)

    bad_checks = 0
    last_switch_time = 0

    while True:

        try:

            current = get_current_wifi()

            if not current:
                print("\nNo Wi-Fi connection detected.")

                time.sleep(CHECK_INTERVAL)
                continue

            # ------------------------------------------------
            # Make sure we're monitoring one of our networks
            # ------------------------------------------------

            if current not in WIFI_NETWORKS:
                print(
                    f"\nCurrently connected to "
                    f"'{current}', which isn't in our monitor list."
                )

                break

            # ------------------------------------------------
            # Test current Wi-Fi
            # ------------------------------------------------

            result = check_current_network()

            log_status(result)

            current_score = result["score"]

            # ------------------------------------------------
            # Determine whether current network is bad
            # ------------------------------------------------

            if current_score < 50:

                bad_checks += 1

                print(
                    f"Bad connection detected "
                    f"({bad_checks}/{BAD_CHECKS_BEFORE_SWITCH})"
                )

            else:

                bad_checks = 0

            # ------------------------------------------------
            # Need multiple bad checks before switching
            # ------------------------------------------------

            if bad_checks < BAD_CHECKS_BEFORE_SWITCH:

                time.sleep(CHECK_INTERVAL)
                continue

            # ------------------------------------------------
            # Cooldown
            # ------------------------------------------------

            elapsed = time.time() - last_switch_time

            if elapsed < COOLDOWN_AFTER_SWITCH:

                remaining = int(
                    COOLDOWN_AFTER_SWITCH - elapsed
                )

                print(
                    f"Switch cooldown active "
                    f"({remaining}s remaining)"
                )

                time.sleep(CHECK_INTERVAL)
                continue

            # ------------------------------------------------
            # Identify alternative network
            # ------------------------------------------------

            alternatives = [
                network
                for network in WIFI_NETWORKS
                if network != current
            ]

            if not alternatives:

                time.sleep(CHECK_INTERVAL)
                continue

            # ------------------------------------------------
            # Test alternative network
            #
            # We have to temporarily connect to it to measure
            # its actual internet quality.
            # ------------------------------------------------

            best_network = None
            best_score = -1

            for network in alternatives:

                print(
                    f"\nTesting alternative network: "
                    f"{network}"
                )

                switched = switch_wifi(network)

                if not switched:
                    continue

                test = check_current_network()

                log_status(test)

                if test["score"] > best_score:

                    best_score = test["score"]
                    best_network = network

            # ------------------------------------------------
            # Decide where to stay
            # ------------------------------------------------

            if best_network is not None:

                print(
                    f"\nBest alternative: "
                    f"{best_network} "
                    f"(score {best_score}/100)"
                )

                if best_score >= 50:

                    print(
                        f">>> Staying on {best_network}"
                    )

                else:

                    print(
                        ">>> Neither network has a "
                        "healthy connection."
                    )

            else:

                print(
                    ">>> Could not connect to an alternative."
                )

            bad_checks = 0
            last_switch_time = time.time()

            time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:

            print("\nStopped by user.")
            break

        except Exception as e:

            print(f"\nUnexpected error: {e}")

            time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
