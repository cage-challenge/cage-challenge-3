from CybORG import CybORG
import inspect


# Set up CybORG
print("Setup")
path = str(inspect.getfile(CybORG))
path = path[:-7] + f'/Shared/Scenarios/Scenario1KeyboardRed.yaml' # Change this to pick your agents
cyborg = CybORG(path, 'sim')

for i in range(1):
    print(f"Game: {i}")
    cyborg.start(1000)
    cyborg.reset()

