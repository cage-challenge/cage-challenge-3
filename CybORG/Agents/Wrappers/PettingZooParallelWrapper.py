from typing import Optional, Tuple

import numpy as np
from gym import spaces

from CybORG import CybORG
from CybORG.Agents.Wrappers import BaseWrapper
from CybORG.Simulator.Actions.ConcreteActions.ControlTraffic import BlockTraffic, AllowTraffic
from CybORG.Simulator.Actions.ConcreteActions.RemoveOtherSessions import RemoveOtherSessions
from CybORG.Simulator.Actions.ConcreteActions.ExploitActions.RetakeControl import RetakeControl
from CybORG.Simulator.Actions import Sleep


class PettingZooParallelWrapper(BaseWrapper):

    def __init__(self, env: CybORG,):
        super().__init__(env)
        self._agent_ids = self.possible_agents
        # assuming that the final value in the agent name indicates which drone that agent is on
        self.agent_host_map = {agent_name: f'drone_{agent_name.split("_")[-1]}' for agent_name in self.possible_agents}
        # get all ip_addresses
        self.ip_addresses = list(self.env.get_ip_map().values())
        num_drones = len(self.ip_addresses)
        self._action_spaces = {agent: spaces.Discrete(len(self.get_action_space(agent))) for agent in
                               self.possible_agents}
        # success + own_drone(block Ips + processes + network conns + pos) + other_drones(IPs + session_+pos)
        self._observation_spaces = {agent_name: spaces.MultiDiscrete(
            [3] + [2 for i in range(num_drones)] + [2] + [3 for i in range(num_drones)] + [101, 101] + (
                    num_drones - 1) * [num_drones, 101, 101, 2]) for agent_name in self.possible_agents}
        self.msg_len = 0
        self.metadata = {"render_modes": ["human", "rgb_array"], "name": "Cage_Challenge_3"}
        #self.agent_actions = self.int_to_cyborg_action()
        self.dones = {agent: False for agent in self.possible_agents}
        self.rewards = {agent: 0. for agent in self.possible_agents}
        self.infos = {}

    def reset(self,
              seed: Optional[int] = None,
              return_info: bool = False,
              options: Optional[dict] = None) -> dict:
        res = self.env.reset()
        #self.agent_actions = self.int_to_cyborg_action()
        self.dones = {agent: False for agent in self.possible_agents}
        self.rewards = {agent: 0. for agent in self.possible_agents}
        self.infos = {}
        # assuming that the final value in the agent name indicates which drone that agent is on
        #self.int_to_action = self.int_to_cyborg_action()
        self.agent_host_map = {agent_name: f'drone_{agent_name.split("_")[-1]}' for agent_name in self.possible_agents}
        self.ip_addresses = list(self.env.get_ip_map().values())
        return {agent: self.observation_change(agent, obs=self.env.get_observation(agent)) for agent in self.agents}

    def step(self, actions: dict) -> Tuple[dict, dict, dict, dict]:
        actions, msgs = self.select_messages(actions)
        actions_dict = {}

        for agent, act in actions.items():
            assert self.action_space(agent).contains(act)
            #actions_dict[agent] = self.agent_actions[agent][act]
            actions_dict[agent] = self.int_to_cyborg_action(agent, act)   

        raw_obs, rews, dones, infos = self.env.parallel_step(actions_dict, messages=msgs)
        # green_agents = {agent: if }
        # rews = GreenAvailabilityRewardCalculator(raw_obs, ['green_agent_0','green_agent_1', 'green_agent_2' ]).calculate_reward()
        obs = {agent: self.observation_change(agent, raw_agent_obs) for agent, raw_agent_obs in raw_obs.items()}
        # obs = {agent: self.observation_change(agent, obs) for agent in self.possible_agents}
        # set done to true if maximumum steps are reached
        self.dones.update(dones)
        self.rewards = {agent: float(sum(agent_rew.values()))/len(rews.items()) for agent, agent_rew in rews.items()}
        #self.rewards = {agent: float(sum(agent_rew.values())) for agent, agent_rew in rews.items()}
        # send messages
        return obs, self.rewards, dones, infos

    def parse_message(self, message: list, agent_name: str):
        return []

    def select_messages(self, action):
        return action, {}

    def render(self, mode="human"):
        # Insert code from phillip
        return self.env.render(mode)

    def close(self):
        # Insert code from phillip
        return self.env.close()

    @property
    def observation_spaces(self):
        '''
        Returns the observation space for every possible agent
        '''
        try:
            return {agent: self.observation_space(agent) for agent in self.possible_agents}
        except AttributeError:
            raise AttributeError(
                "The base environment does not have an `observation_spaces` dict attribute. Use the environments `observation_space` method instead"
            )

    @property
    def action_spaces(self):
        '''
        Returns the action space for every possible agent
        '''
        try:
            return {agent: self.action_space(agent) for agent in self.possible_agents}
        except AttributeError:
            raise AttributeError(
                "The base environment does not have an action_spaces dict attribute. Use the environments `action_space` method instead"
            )

    def get_rewards(self):
        '''
        Returns the rewards for every possible agent
        '''
        try:
            return {agent: self.get_reward(agent) for agent in self.possible_agents}
        except AttributeError:
            raise AttributeError(
                "The base environment does not have an action_spaces dict attribute. Use the environments `action_space` method instead"
            )

    def get_dones(self):
        '''
        Returns the dones for every possible agent
        '''
        try:
            return {agent: self.get_done(agent) for agent in self.possible_agents}
        except AttributeError:
            raise AttributeError(
                "The base environment does not have an action_spaces dict attribute. Use the environments `action_space` method instead"
            )

    def observation_space(self, agent: str):
        '''
        Returns the observation space for a single agent

        Parameters:
            agent -> str
        '''
        return self._observation_spaces[agent]

    def action_space(self, agent: str):
        '''
        Returns the action space for a single agent

        Parameters:
            agent -> str
        '''
        return self._action_spaces[agent]

    def get_reward(self, agent):
        '''
        Returns the reward for a single agent

        Parameters:
            agent -> str
        '''
        return self.rewards[agent]

    def get_done(self, agent):
        '''
        Returns the dones for a single agent

        Parameters:
            agent -> str
        '''
        return self.dones[agent]

    def int_to_cyborg_action_old(self):
        '''
        Returns a dictionary containing dictionaries that maps the number selected by the agent to a specific CybORG action

        '''
        cyborg_agent_actions = {}
        for agent in self.active_agents:
            cyborg_action_to_int = {}
            act_count = 0
            for action in self.env.get_action_space(self.active_agents[0])['action'].keys():
                params_dict = {}
                if action.__name__ == 'Sleep':
                    cyborg_action_to_int[act_count] = Sleep()
                    act_count+=1
                elif action.__name__ == 'RemoveOtherSessions':
                    params_dict['agent'] = agent
                    params_dict['session'] = 0
                    cyborg_action_to_int[act_count] = action(**params_dict)
                    act_count+=1
                else:
                    for ip in self.env.get_action_space(self.active_agents[0])['ip_address'].keys():
                        for sess in self.env.get_action_space(self.active_agents[0])['session'].keys():
                            if sess == 0:
                                params_dict['session'] = 0
                                params_dict['ip_address'] = ip
                                params_dict['agent'] = agent
                                cyborg_action_to_int[act_count] = action(**params_dict)
                                act_count+=1
            cyborg_agent_actions[agent] = cyborg_action_to_int
        return cyborg_agent_actions
    
    def int_to_cyborg_action(self, agent, action_int):
        '''
        Returns the CybORG action corresponding to the action_int selected by the agent

        '''
        if action_int == 55:
            return Sleep()
        elif action_int == 18:
            return RemoveOtherSessions(session=0, agent=agent)
        else:
            if action_int >= 0 and action_int < 18:
                return RetakeControl(session=0, agent=agent, ip_address=self.ip_addresses[action_int])
            elif action_int >= 19 and action_int < 37:
                return BlockTraffic(session=0, agent=agent, ip_address=self.ip_addresses[action_int-19])
            elif action_int >= 37 and action_int < 55:
                return AllowTraffic(session=0, agent=agent, ip_address=self.ip_addresses[action_int-37])
    
    def get_action_space(self, agent):
        '''
        Obtains the action_space of the specified agent

        Parameters:
            agent -> str
        '''
        initial = self.env.get_action_space(agent)
        this_agent = agent
        unmasked_as = []
        agent_actions = []

        for key in initial.copy():
            if key != 'action':
                del initial[key]

        init_list = list(initial['action'].items())
        for i in range(len(init_list)):
            agent_actions.append(init_list[i][0].__name__)

        for act in agent_actions:
            if act == 'Sleep':
                unmasked_as.append('Sleep')
            elif act == 'RemoveOtherSessions':
                unmasked_as.append(f'RemoveOtherSessions {this_agent}')
            else:
                for agent in self.agent_host_map.values():
                    unmasked_as.append(f"{act} {agent}")
        return unmasked_as

    def observation_change(self, agent: str, obs: dict):
        '''Initialises the observation space for the agent (if undefined) or modifies the observation space (if defined)

        Parameters:
            agent -> str

        OG_obs -> None/np.array
            None if undefined
            np.array if defined
        '''
        # assuming that the final value in the agent name indicates which drone that agent is on
        if 'agent' in agent:
            self.agent_host_map = {agent_name: f'drone_{agent_name.split("_")[-1]}' for agent_name in self.possible_agents}
            # get all ip_addresses
            self.ip_addresses = list(self.env.get_ip_map().values())
            num_drones = len(self.ip_addresses)
            obs_length = int(1 + num_drones + 1 + num_drones + 2 + (num_drones - 1) * (2 + 1 + 1) + self.msg_len)
            new_obs = np.zeros(obs_length, dtype=int)
            if obs is not None:
                own_host_name = self.agent_host_map[agent]
                # obs_length = success + own_drone(block Ips + processes + network conns) + other_drones_including_own(IPs + session_ + pos)
                # element location --> [0, 1,...,num_drones, 1+num_drones, 2+num_drones, ..., 2+2*num_drones, 3+2*num_drones, 4+2*num_drones,...,4+4*num_drones]
                index = 0
                # success
                new_obs[index] = obs['success'].value - 1
                index += 1

                if agent in self.env.active_agents:
                    # Add blocked IPs
                    for i, ip in enumerate(self.ip_addresses):
                        new_obs[index + i] = 1 if ip in [blocked_ip for interface in
                                                         obs[own_host_name]['Interface'] if
                                                         'blocked_ips' in interface for blocked_ip in interface['blocked_ips']] else 0
                    index += len(self.ip_addresses)

                    # add flagged malicious processes
                    new_obs[index] = 1 if 'Processes' in obs[own_host_name] else 0
                    index += 1
                    # add flagged messages
                    for i, ip in enumerate(self.ip_addresses):
                        new_obs[index + i] = 1 if ip in [network_conn['remote_address']
                                                         for interface in obs[own_host_name]['Interface']
                                                         if 'NetworkConnections' in interface
                                                         for network_conn in interface['NetworkConnections']] \
                            else 0
                    index += len(self.ip_addresses)

                    pos = obs[own_host_name]['System info'].get('position', (0, 0))
                    new_obs[index] = max(int(pos[0]), 0)
                    new_obs[index + 1] = max(int(pos[1]), 0)
                    index += 2
                    ip_host_map = {ip: host for host, ip in self.env.get_ip_map().items()}
                    # add information of other drones
                    for i, ip in enumerate(self.ip_addresses):
                        hostname = ip_host_map[ip]
                        if hostname != own_host_name:
                            new_obs[index] = i
                            index += 1
                            # add position of drone
                            if hostname in obs:
                                pos = obs[hostname]['System info'].get('position', (0, 0))
                                new_obs[index] = max(int(pos[0]), 0)
                                new_obs[index + 1] = max(int(pos[1]), 0)
                                index += 2
                                # add session to drone
                                new_obs[index] = 1 if 'Sessions' in obs[hostname] else 0
                                index += 1
                            else:
                                new_obs[index] = 0
                                new_obs[index + 1] = 0
                                new_obs[index + 2] = 0
                                index += 3

                    msg = self.parse_message(obs['message'] if 'message' in obs else [], agent)
                    if len(msg) > 0:
                        for j in range(len(msg)):
                            new_obs[index+j] = msg[j]
                        index += len(msg)
                # update data of other drones
                # try:
                assert self._observation_spaces[agent].contains(
                    new_obs), f'Observation \n{new_obs}\n is not contained within Observation Space \n{self._observation_spaces[agent]}\n for agent {agent}'
                # except AssertionError:
                #     breakpoint()
            return new_obs

    def get_attr(self, attribute: str):
        return self.env.get_attr(attribute)

    def get_last_actions(self, agent):
        return self.get_attr('get_last_action')(agent)

    @property
    def agents(self):
        return [agent for agent in self.env.active_agents if not self.dones[agent]]

    @property
    def possible_agents(self):
        return self.env.agents

