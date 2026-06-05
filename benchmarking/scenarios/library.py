from benchmarking.scenario import BenchmarkScenario, ScenarioEvent
from reference_engine.models import Side, OrderType, TimeInForce

def _base_payload(seq: int, ts: int, order_id: int, side: Side, price: int, qty: int, tif: TimeInForce = TimeInForce.GTC, party_id: str = None) -> dict:
    return {
        "sequence_no": seq,
        "timestamp_ns": ts,
        "order_id": order_id,
        "client_order_id": f"c{order_id}",
        "symbol": "TEST",
        "side": side.name,
        "order_type": OrderType.LIMIT.name,
        "price": price,
        "quantity": qty,
        "tif": tif.name,
        "party_id": party_id or f"p{order_id}",
        "stop_price": None
    }

def get_simple_fill_scenario() -> BenchmarkScenario:
    return BenchmarkScenario(
        scenario_id="simple_fill_001",
        name="Simple Fill",
        description="BUY 100 @ 50, SELL 100 @ 50",
        seed=1001,
        events=[
            ScenarioEvent(1000, "NewOrderRequest", _base_payload(1, 1000, 1, Side.BUY, 50, 100)),
            ScenarioEvent(2000, "NewOrderRequest", _base_payload(2, 2000, 2, Side.SELL, 50, 100))
        ]
    )

def get_partial_fill_scenario() -> BenchmarkScenario:
    return BenchmarkScenario(
        scenario_id="partial_fill_001",
        name="Partial Fill",
        description="BUY 100 @ 50, SELL 20 @ 50",
        seed=1002,
        events=[
            ScenarioEvent(1000, "NewOrderRequest", _base_payload(1, 1000, 1, Side.BUY, 50, 100)),
            ScenarioEvent(2000, "NewOrderRequest", _base_payload(2, 2000, 2, Side.SELL, 50, 20))
        ]
    )

def get_fifo_scenario() -> BenchmarkScenario:
    return BenchmarkScenario(
        scenario_id="fifo_001",
        name="FIFO",
        description="BUY1 100 @ 50, BUY2 100 @ 50, SELL 150 @ 50",
        seed=1003,
        events=[
            ScenarioEvent(1000, "NewOrderRequest", _base_payload(1, 1000, 1, Side.BUY, 50, 100)),
            ScenarioEvent(2000, "NewOrderRequest", _base_payload(2, 2000, 2, Side.BUY, 50, 100)),
            ScenarioEvent(3000, "NewOrderRequest", _base_payload(3, 3000, 3, Side.SELL, 50, 150))
        ]
    )

def get_multi_level_fill_scenario() -> BenchmarkScenario:
    return BenchmarkScenario(
        scenario_id="multi_level_fill_001",
        name="Multi-Level Fill",
        description="SELL 20 @ 50, SELL 30 @ 51, SELL 40 @ 52, BUY 70 @ 52",
        seed=1004,
        events=[
            ScenarioEvent(1000, "NewOrderRequest", _base_payload(1, 1000, 1, Side.SELL, 50, 20)),
            ScenarioEvent(2000, "NewOrderRequest", _base_payload(2, 2000, 2, Side.SELL, 51, 30)),
            ScenarioEvent(3000, "NewOrderRequest", _base_payload(3, 3000, 3, Side.SELL, 52, 40)),
            ScenarioEvent(4000, "NewOrderRequest", _base_payload(4, 4000, 4, Side.BUY, 52, 70))
        ]
    )

def get_cancel_scenario() -> BenchmarkScenario:
    return BenchmarkScenario(
        scenario_id="cancel_001",
        name="Cancel",
        description="BUY 100, SELL 40, CANCEL BUY",
        seed=1005,
        events=[
            ScenarioEvent(1000, "NewOrderRequest", _base_payload(1, 1000, 1, Side.BUY, 50, 100)),
            ScenarioEvent(2000, "NewOrderRequest", _base_payload(2, 2000, 2, Side.SELL, 50, 40)),
            ScenarioEvent(3000, "CancelOrderRequest", {
                "sequence_no": 3,
                "timestamp_ns": 3000,
                "order_id": 1,
                "client_order_id": "c1",
                "symbol": "TEST"
            })
        ]
    )

def get_replace_scenario() -> BenchmarkScenario:
    return BenchmarkScenario(
        scenario_id="replace_001",
        name="Replace",
        description="BUY 100, REPLACE to 150 @ 51",
        seed=1006,
        events=[
            ScenarioEvent(1000, "NewOrderRequest", _base_payload(1, 1000, 1, Side.BUY, 50, 100)),
            ScenarioEvent(2000, "ReplaceOrderRequest", {
                "sequence_no": 2,
                "timestamp_ns": 2000,
                "original_order_id": 1,
                "new_order_id": 2,
                "new_price": 51,
                "new_quantity": 150,
                "symbol": "TEST",
                "client_order_id": "c2"
            })
        ]
    )

def get_ioc_scenario() -> BenchmarkScenario:
    return BenchmarkScenario(
        scenario_id="ioc_001",
        name="IOC",
        description="SELL 50, BUY 100 IOC (should fill 50, cancel 50)",
        seed=1007,
        events=[
            ScenarioEvent(1000, "NewOrderRequest", _base_payload(1, 1000, 1, Side.SELL, 50, 50)),
            ScenarioEvent(2000, "NewOrderRequest", _base_payload(2, 2000, 2, Side.BUY, 50, 100, tif=TimeInForce.IOC))
        ]
    )

def get_fok_scenario() -> BenchmarkScenario:
    return BenchmarkScenario(
        scenario_id="fok_001",
        name="FOK",
        description="SELL 50, BUY 100 FOK (should cancel 100)",
        seed=1008,
        events=[
            ScenarioEvent(1000, "NewOrderRequest", _base_payload(1, 1000, 1, Side.SELL, 50, 50)),
            ScenarioEvent(2000, "NewOrderRequest", _base_payload(2, 2000, 2, Side.BUY, 50, 100, tif=TimeInForce.FOK))
        ]
    )

def get_smp_scenario() -> BenchmarkScenario:
    return BenchmarkScenario(
        scenario_id="smp_001",
        name="SMP",
        description="BUY 100 (p1), SELL 100 (p1) -> Should trigger Self Match Prevention",
        seed=1009,
        events=[
            ScenarioEvent(1000, "NewOrderRequest", _base_payload(1, 1000, 1, Side.BUY, 50, 100, party_id="p1")),
            ScenarioEvent(2000, "NewOrderRequest", _base_payload(2, 2000, 2, Side.SELL, 50, 100, party_id="p1"))
        ]
    )

def get_large_book_scenario() -> BenchmarkScenario:
    events = []
    # Build 100 bids and 100 asks
    for i in range(100):
        # bids from 10 to 109, asks from 200 to 299
        events.append(ScenarioEvent(1000 + i*10, "NewOrderRequest", _base_payload(1 + i*2, 1000 + i*10, 1 + i*2, Side.BUY, 10 + i, 10)))
        events.append(ScenarioEvent(1005 + i*10, "NewOrderRequest", _base_payload(2 + i*2, 1005 + i*10, 2 + i*2, Side.SELL, 200 + i, 10)))
    
    # Sweep
    events.append(ScenarioEvent(50000, "NewOrderRequest", _base_payload(999, 50000, 999, Side.BUY, 250, 1000)))
    
    return BenchmarkScenario(
        scenario_id="large_book_001",
        name="Large Book Sweep",
        description="100 bids, 100 asks, then a large sweep crossing half the asks",
        seed=1010,
        events=events
    )

def get_all_scenarios():
    return [
        get_simple_fill_scenario(),
        get_partial_fill_scenario(),
        get_fifo_scenario(),
        get_multi_level_fill_scenario(),
        get_cancel_scenario(),
        get_replace_scenario(),
        get_ioc_scenario(),
        get_fok_scenario(),
        get_smp_scenario(),
        get_large_book_scenario()
    ]
