from benchmarking.models import ScenarioDefinition

def get_standard_scenario() -> ScenarioDefinition:
    return ScenarioDefinition(
        "SCENARIO_1", 
        "Standard load test",
        [{"action": "CONNECT"}, {"action": "SUBMIT_ORDER"}, {"action": "DISCONNECT"}]
    )
