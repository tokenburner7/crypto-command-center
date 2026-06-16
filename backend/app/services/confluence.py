"""2-signal confluence engine with calibration AND-gate and narrative generation."""
import json
import time
from app.repositories.whale_repo import WhaleRepository
from app.repositories.stablecoin_repo import StablecoinRepository
from app.database import get_db

WEIGHTS = {"whale_activity": 0.55, "stablecoin_flow": 0.45}

MIN_DATA_POINTS = 100
MIN_RUNTIME_HOURS = 48
FRESHNESS_HOURS = 1

_start_time = time.time()

async def _check_calibration() -> dict:
    whale_data = await WhaleRepository.count_recent(hours=99999)
    supply_data = await StablecoinRepository.get_latest()
    
    whale_count = whale_data.get("count", 0) or 0
    supply_count = len(supply_data) * (await _estimate_supply_readings())
    
    runtime_hours = (time.time() - _start_time) / 3600
    
    whale_fresh = await WhaleRepository.count_recent(hours=FRESHNESS_HOURS)
    supply_fresh = len(await StablecoinRepository.get_latest()) > 0
    
    conditions = {
        "whale_datapoints": {"met": whale_count >= MIN_DATA_POINTS, "current": whale_count, "target": MIN_DATA_POINTS},
        "stablecoin_datapoints": {"met": supply_count >= MIN_DATA_POINTS, "current": supply_count, "target": MIN_DATA_POINTS},
        "runtime": {"met": runtime_hours >= MIN_RUNTIME_HOURS, "current": round(runtime_hours, 1), "target": MIN_RUNTIME_HOURS},
        "freshness": {"met": (whale_fresh.get("count", 0) or 0) > 0 and supply_fresh},
    }
    
    all_met = all(c["met"] for c in conditions.values())
    return {
        "calibrated": all_met,
        "conditions_met": sum(1 for c in conditions.values() if c["met"]),
        "conditions_total": len(conditions),
        "conditions": conditions,
    }

async def _estimate_supply_readings():
    db = await get_db()
    cursor = await db.execute("SELECT COUNT(DISTINCT timestamp) as cnt FROM stablecoin_supply")
    row = await cursor.fetchone()
    await db.close()
    return row["cnt"] if row else 0

async def compute_confluence() -> dict:
    calibration = await _check_calibration()
    now = int(time.time())
    
    if not calibration["calibrated"]:
        return {
            "overall_score": 0.0,
            "signal": "CALIBRATING",
            "direction": "STABLE",
            "calibration_status": "calibrating",
            "calibration_progress": calibration,
            "narrative": _calibration_narrative(calibration),
            "components": [],
            "timestamp": now,
        }
    
    whale_score, whale_desc = await _whale_signal()
    stable_score, stable_desc = await _stablecoin_signal()
    
    overall = whale_score * WEIGHTS["whale_activity"] + stable_score * WEIGHTS["stablecoin_flow"]
    
    if overall > 0.65:
        signal = "STRONG"
    elif overall > 0.35:
        signal = "MODERATE"
    else:
        signal = "WEAK"
    
    db = await get_db()
    cursor = await db.execute("SELECT overall_score FROM signal_confluences WHERE calibration_status='calibrated' ORDER BY timestamp DESC LIMIT 1")
    prev = await cursor.fetchone()
    await db.close()
    prev_score = prev["overall_score"] if prev else overall
    delta = overall - prev_score
    direction = "RISING" if delta > 0.05 else "FALLING" if delta < -0.05 else "STABLE"
    
    components = [
        {"name": "Whale Activity", "score": round(whale_score, 2), "detail": whale_desc},
        {"name": "Stablecoin Flows", "score": round(stable_score, 2), "detail": stable_desc},
    ]
    
    narrative = _generate_narrative(whale_score, stable_score, signal, direction)
    
    db = await get_db()
    await db.execute(
        "INSERT INTO signal_confluences (overall_score, signal, direction, calibration_status, narrative, components, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (round(overall, 3), signal, direction, "calibrated", narrative, json.dumps(components), now)
    )
    await db.commit()
    await db.close()
    
    return {
        "overall_score": round(overall, 3),
        "signal": signal,
        "direction": direction,
        "calibration_status": "calibrated",
        "narrative": narrative,
        "components": components,
        "timestamp": now,
    }

async def _whale_signal() -> tuple:
    data = await WhaleRepository.count_recent(hours=1)
    count = data.get("count", 0) or 0
    avg = data.get("avg_amount", 0) or 0
    if count > 10 and avg > 5_000_000:
        return (0.8, f"{count} large txns, avg ${avg:,.0f}")
    elif count > 5:
        return (0.5, f"{count} significant txns")
    elif count > 0:
        return (0.2, f"{count} txns detected")
    return (0.0, "No recent whale activity")

async def _stablecoin_signal() -> tuple:
    supply = await StablecoinRepository.get_latest()
    total = sum(s["total_supply_usd"] or 0 for s in supply)
    total_change = sum(s["change_24h_usd"] or 0 for s in supply)
    if total_change > 2_000_000_000:
        return (0.8, f"Supply growing fast (+${total_change/1e9:.1f}B), total ${total/1e9:.1f}B")
    elif total_change > 0:
        return (0.6, f"Supply growing (+${total_change/1e6:.0f}M), total ${total/1e9:.1f}B")
    elif total_change > -1_000_000_000:
        return (0.4, f"Supply stable, total ${total/1e9:.1f}B")
    else:
        return (0.2, f"Supply contracting (${total_change/1e9:.1f}B), total ${total/1e9:.1f}B")

def _calibration_narrative(cal: dict) -> str:
    met = cal["conditions_met"]
    total = cal["conditions_total"]
    return f"Calibrating ({met}/{total}): collecting data to establish signal baselines"

def _generate_narrative(whale: float, stable: float, signal: str, direction: str) -> str:
    parts = []
    if whale > 0.6:
        parts.append("Whales accumulating")
    elif whale > 0.3:
        parts.append("Moderate whale activity")
    else:
        parts.append("Whales quiet")
    
    if stable > 0.6:
        parts.append("stablecoin supply growing")
    elif stable > 0.3:
        parts.append("stablecoin supply stable")
    else:
        parts.append("stablecoin supply contracting")
    
    return f"{', '.join(parts)} — {signal} {direction}"
