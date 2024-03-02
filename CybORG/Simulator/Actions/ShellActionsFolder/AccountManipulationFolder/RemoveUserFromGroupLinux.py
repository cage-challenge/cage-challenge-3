# Copyright DST Group. Licensed under the MIT license.
from CybORG.Simulator.Actions.ShellActionsFolder.AccountManipulationFolder.AccountManipulation import AccountManipulation
from CybORG.Shared.Enums import OperatingSystemType
from CybORG.Shared.Observation import Observation


class RemoveUserFromGroupLinux(AccountManipulation):
    def __init__(self, session, agent, username, group):
        super().__init__(session, agent)
        self.user = username
        self.group = group

    def execute(self, state):
        obs = Observation()
        obs.set_success(False)
        if self.session not in state.sessions[self.agent]:
            return obs

        if state.sessions[self.agent][self.session].active:
            host = state.sessions[self.agent][self.session].hostname
            obs.add_system_info(hostid="hostid0", os_type=host.os_type)
            if host.os_type == OperatingSystemType.LINUX:
                host.remove_user_group(user=self.user, group=self.group)
                obs.set_success(True)
            else:
                obs.set_success(False)
        else:
            obs.set_success(False)
        return obs
