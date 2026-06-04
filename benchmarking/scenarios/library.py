from benchmarking.scenario import BenchmarkScenario, ScenarioEvent
from reference_engine.models import Side, OrderType, TimeInForce

def _base_payload(seq: int, ts: int, order_id: int, side: Side, price: int, qty: int) -> dict:
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
        "tif": TimeInForce.GTC.name,
        "party_id": f"p{order_id}",
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

def get_all_scenarios():
    return [
        get_simple_fill_scenario(),
        get_partial_fill_scenario(),
        get_fifo_scenario(),
        get_multi_level_fill_scenario(),
        get_cancel_scenario()
    ]
