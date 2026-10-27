import os
import sys

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time
import random
from src.defense.orchestrator import DefenseOrchestrator



def simulate_session(orchestrator: DefenseOrchestrator, is_attacker: bool = False, total_keys: int = 50):
    user_name = "sysadmin_ali"
    session_id = f"sess_{user_name}_{random.randint(1000, 9999)}"
    src_ip = "192.168.1.150" if not is_attacker else "203.0.113.42"

    print("\n" + "="*60)
    print(f"[*] Starting session simulation: {session_id}")
    print(f"[*] Identity: {'[SUSPICIOUS / ATTACKER]' if is_attacker else '[LEGITIMATE OWNER]'}")
    print(f"[*] Source IP: {src_ip}")
    print("="*60)

    latencies = []

    for i in range(1, total_keys + 1):
        # Timing characteristics
        if not is_attacker:
            # Fluent, natural typing (mean ~115ms, low deviation)
            flight_time = random.gauss(115.0, 15.0)
            dwell_time = random.gauss(70.0, 8.0)
        else:
            # Impostor: Hesitant, irregular, or pasting long bursts
            flight_time = random.choice([random.gauss(280.0, 60.0), random.uniform(400.0, 900.0), 20.0])
            dwell_time = random.gauss(110.0, 30.0)

        flight_time = max(10.0, flight_time)
        dwell_time = max(10.0, dwell_time)

        event = {
            "user": user_name,
            "session_id": session_id,
            "src_ip": src_ip,
            "timestamp_ms": int(time.time() * 1000),
            "flight_time_ms": flight_time,
            "dwell_ms": dwell_time,
            "key_code": random.randint(32, 126)
        }

        result = orchestrator.process_keystroke_event(event)

        if result.get("status") != "buffering":
            latencies.append(result["latency_ms"])
            print(f"  Key #{i:02d} | Risk Score: {result['risk_score']:.3f} | "
                  f"Action: {result['action']:<18} | Latency: {result['latency_ms']:.2f}ms")

            if result["action"] in ["TERMINATE_SESSION", "ISOLATE_IP"]:
                print(f"[!] Session successfully neutralized at keystroke #{i}!")
                break

        # Simulated real typing interval
        time.sleep(min(flight_time / 1000.0, 0.05))  # Accelerated for fast benchmarking

    if latencies:
        avg_lat = sum(latencies) / len(latencies)
        max_lat = max(latencies)
        print(f"\n[+] Benchmark Summary: Avg Latency: {avg_lat:.2f}ms (Max: {max_lat:.2f}ms) - SLA <500ms: {'PASSED' if max_lat < 500 else 'FAILED'}")


if __name__ == "__main__":
    print("[*] Initializing Autonomous Cyber Defense Pipeline...")
    orc = DefenseOrchestrator()

    # Test 1: Normal authorized user typing
    simulate_session(orc, is_attacker=False, total_keys=45)

    # Test 2: Attacker with stolen credentials typing
    simulate_session(orc, is_attacker=True, total_keys=45)
