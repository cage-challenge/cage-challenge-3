
from typing import Tuple, List, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass

from CybORG.Shared import Observation
from CybORG.Simulator.Actions import Action
from CybORG.Shared.Enums import DecoyType, OperatingSystemType
from CybORG.Simulator.Host import Host
from CybORG.Simulator.Session import Session
from CybORG.Simulator.State import State
from CybORG.Simulator.Actions.AbstractActions.Misinform import Decoy, DecoyFactory, _is_host_using_port


class HarakaDecoyFactory(DecoyFactory):
    """
    Assembles process information to appear as an apache server
    """
    def make_decoy(self, host: Host) -> Decoy:
        del host
        return Decoy(service_name="haraka", name="haraka",
                open_ports=[{'local_port':25, 'local_address':'0.0.0.0'}],
                process_type="smtp",
                process_path="/usr/sbin",
                version="haraka 2.7.0")

    def is_host_compatible(self, host: Host) -> bool:
        has_port = not _is_host_using_port(host, 25)
        is_linux = host.os_type == OperatingSystemType.LINUX

        return all((has_port, is_linux))
haraka_decoy_factory = HarakaDecoyFactory()

class DecoyHarakaSMPT(Action):
    """
    Creates a misleading process on the designated host depending on
    available and compatible options.
    """
    def __init__(self, *, session: int, agent: str, hostname: str):
        super().__init__()
        self.agent = agent
        self.session = session
        self.hostname = hostname
        self.decoy_type = DecoyType.EXPLOIT
        self.candidate_decoys = (haraka_decoy_factory,)

    

    def execute(self, state: State) -> Observation:
        obs_fail = Observation(False)
        obs_succeed = Observation(True)

        sessions = [s for s in state.sessions[self.agent].values() if
                    s.hostname == self.hostname]
        if len(sessions) == 0:
            return obs_fail

        session = state.np_random.choice(sessions)
        host = state.hosts[self.hostname]

        try:
            decoy_factory = self.__select_one_factory(host, state)
            decoy = decoy_factory.make_decoy(host)
            self.__create_process(obs_succeed, session, host, decoy)
            #print ("Misinform Success. Result: {}".format(result))

            return obs_succeed

        except RuntimeError:
            #print ("Misinform FAILURE")
            return obs_fail


    def __select_one_factory(self, host: Host, state: State) -> DecoyFactory:
        """
        Examines all decoy factories and returns one randomly compatible one.
        Raises RuntimeError if no compatible ones are found.
        """

        compatible_factories = [factory for factory in self.candidate_decoys
                if factory.is_host_compatible(host) ]

        if len(compatible_factories) == 0:
            raise RuntimeError("No compatible factory")

        return state.np_random.choice(list(compatible_factories))

    def __create_process(self, obs: Observation, sess: Session, host: Host,
            decoy: Decoy) -> None:
        """
        Creates a process & service from Decoy on current host, adds it
        to the observation.
        """

        parent_pid = 1

        process_name = decoy.name
        username = sess.username
        version = decoy.version
        open_ports = decoy.open_ports
        process_type = decoy.process_type
        process_props = decoy.properties

        service_name = decoy.service_name

        new_proc = host.add_process(name=process_name, ppid=parent_pid,
                user=username, version=version, process_type=process_type,
                open_ports=open_ports, decoy_type=self.decoy_type,
                properties=process_props)

        host.add_service(service_name=service_name, process=new_proc.pid,
                session=sess)

        obs.add_process(hostid=self.hostname, pid=new_proc.pid,
                parent_pid=parent_pid, name=process_name,
                username=username, service_name=service_name,
                properties=process_props)

    def __str__(self):
        return f"{self.__class__.__name__} {self.hostname}"
