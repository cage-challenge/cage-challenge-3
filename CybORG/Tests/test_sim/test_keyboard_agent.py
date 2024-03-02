import inspect
import random

from CybORG import CybORG
from CybORG.Agents.SimpleAgents.KeyboardAgent import KeyboardAgent
import pytest

from CybORG.Simulator.Scenarios.FileReaderScenarioGenerator import FileReaderScenarioGenerator


@pytest.fixture(scope="function", params=['Scenario1', 'Scenario1b', 'Scenario2'])
def create_keyboard_cyborg_sim(request):
    path = str(inspect.getfile(CybORG))
    path = path[:-7] + f'/Simulator/Scenarios/scenario_files/{request.param}.yaml'
    agent_name = 'Red'
    keyboard_agent = KeyboardAgent()
    sg = FileReaderScenarioGenerator(path)
    cyborg = CybORG(scenario_generator=sg, agents={agent_name: keyboard_agent})
    return cyborg, request.param, agent_name


@pytest.mark.parametrize('input_func', [lambda: str(random.randint(0, 100)), lambda: random.choice(['idk', '0']), lambda: '0', lambda: str(random.randint(0, 5))])
def test_keyboard_agent(create_keyboard_cyborg_sim, capsys, monkeypatch, input_func):
    cyborg, scenario, agent_name = create_keyboard_cyborg_sim
    captured = capsys.readouterr()
    assert type(cyborg.environment_controller.agent_interfaces[agent_name].agent) is KeyboardAgent
    monkeypatch.setattr('builtins.input', lambda _: input_func())
    for i in range(100):
        result = cyborg.step(agent_name)
        captured = capsys.readouterr()
        assert captured.err == ""
        assert captured.out is not None
