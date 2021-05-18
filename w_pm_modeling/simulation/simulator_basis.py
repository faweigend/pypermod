import logging

import numpy as np
from w_pm_hydraulic.agents.three_comp_hyd_agent import ThreeCompHydAgent
from w_pm_modeling.agents.cp_agents.cp_differential_agent_basis import CpDifferentialAgentBasis
from w_pm_modeling.agents.cp_agents.cp_integral_agent_basis import CpIntegralAgentBasis


class SimulatorBasis:
    """
    Contains convenience functions to run simulations with performance modelling agents. Exemplary simulations are
    time-to-exhaustion (TTE) or recovery estimations according to Caen et al. or Sreedhara.
    """
    # the maximal number of steps for a single simulation run
    step_limit = 5000

    @staticmethod
    def get_recovery_ratio_caen(agent, p_exp, p_rec, t_rec):
        """
        Returns recovery ratio of given agent according to Caen et al.'s WB1 -> RB -> WB2 protocol.
        Recovery ratio estimations for given exp, rec intensity and time
        :param agent:
        :param p_exp:
        :param p_rec:
        :param t_rec:
        :return: ratio in percent
        """

        agent.reset()
        hz = agent.hz

        # The handling agent types
        if isinstance(agent, CpIntegralAgentBasis):
            # consider hz setting of agent
            t_rec = t_rec * hz
            # use build-in function of integral agents
            dynamics = agent.get_recovery_dynamics(p_rec, max_t=t_rec)
            ratio = 100.0
            # no recovery if no recovery time
            if t_rec == 0:
                ratio = 0.0
            # if rec_time is not in dynamics recovery is already at 100%
            elif t_rec < len(dynamics):
                ratio = (dynamics[t_rec - 1] / agent.w_p) * 100.0
            return ratio

        elif isinstance(agent, CpDifferentialAgentBasis) or isinstance(agent, ThreeCompHydAgent):
            # WB1 Exhaust...
            agent.set_power(p_exp)
            steps = 0
            while not agent.is_exhausted() and steps < SimulatorBasis.step_limit:
                agent.perform_one_step()
                steps += 1
            wb1_t = agent.get_time()

            if not agent.is_exhausted():
                raise UserWarning("exhaustion not reached!")

            # Recover...
            agent.set_power(p_rec)
            for _ in range(0, int(t_rec * hz)):
                agent.perform_one_step()
            rec_t = agent.get_time()

            # WB2 Exhaust...
            agent.set_power(p_exp)
            steps = 0
            while not agent.is_exhausted() and steps < SimulatorBasis.step_limit:
                agent.perform_one_step()
                steps += 1
            wb2_t = agent.get_time()
            # return ratio of times as recovery ratio
            return ((wb2_t - rec_t) / wb1_t) * 100.0
        else:
            logging.warning("unknown agent type {}".format(agent))

    @staticmethod
    def get_recovery_ratio_sreedhara(agent, p_exp, t_exp, p_rec, t_rec):
        """
        Use the protocol by Sreedhara et al. to estimate recovery
        For example with p_exp as P$:
        2min at P4 -> recovery -> P4 all out. Recovery is (t_WB1 + t_WB2 - 240s) / 240s
        :param agent:
        :param p_exp: exercise intensity
        :param t_exp: time of predicted exhaustion at p_exp
        :param p_rec: recovery intensity
        :param t_rec: recovery duration
        :return: recovery ratio in percent
        """

        # consider simulation hz
        t_exp = float(t_exp * agent.hz)
        t_rec = float(t_rec * agent.hz)

        # estimate recovery ratios for integral agents
        if isinstance(agent, CpIntegralAgentBasis):
            data = [p_exp] * round(t_exp / 2) + [p_rec] * round(t_rec) + [p_exp] * round(t_exp * 1.5)
            w_bal_hist = agent.estimate_w_p_bal_to_data(data)
            t3 = w_bal_hist.index(0)  # time point of exhaustion
            # the equation to estimate recovery from ttes of both bouts
            return ((round(t_exp / 2) + (float(t3) - (round(t_exp / 2) + t_rec)) - t_exp) / t_exp) * 100.0

        elif isinstance(agent, CpDifferentialAgentBasis) or isinstance(agent, ThreeCompHydAgent):
            # start from 0
            agent.reset()

            # recreate Sreedhara setup and exhaust half (this affects recovery speed)
            agent.set_power(p_exp)
            for i in range(round(t_exp / 2)):
                agent.perform_one_step()
            t1 = agent.get_time()

            # recover agent for trial recovery time
            agent.set_power(p_rec)
            for _ in range(round(t_rec)):
                agent.perform_one_step()
            t2 = agent.get_time()

            # fully exhaust agent in second bout
            steps = 0
            agent.set_power(p_exp)
            while agent.is_exhausted() is False and steps < SimulatorBasis.step_limit:
                agent.perform_one_step()
                steps += 1
            t3 = agent.get_time()

            # apply Sreedhara et al.'s equation
            return ((t1 + (t3 - t2) - (t_exp / agent.hz)) / (t_exp / agent.hz)) * 100.0
        else:
            logging.warning("unknown agent type {}".format(agent))

    @staticmethod
    def simulate_test_run(agent):
        """
        Simulate a test run on an artificial course to investigate expenditure and recovery dynamics
        :return:
        """
        # 3 minute intervals considering the hz setting of the agent
        inter = 180 * agent.hz

        # the power demands over the artificial course
        course = [100] * inter + \
                 [250] * inter + \
                 [100] * inter + \
                 [250] * inter + \
                 [50] * inter + \
                 [50] * inter + \
                 [50] * inter + \
                 [300] * inter + \
                 [200] * inter

        agent.reset()

        times = np.arange(0, len(course)) / agent.hz

        # differentiate between integral and differential agent
        if isinstance(agent, CpIntegralAgentBasis):
            w_bal_hist = agent.estimate_w_p_bal_to_data(course)
            return times, course, w_bal_hist

        elif isinstance(agent, CpDifferentialAgentBasis):
            balances, powers = [], []
            for tick in course:
                agent.set_power(tick)
                powers.append(agent.perform_one_step())
                balances.append(agent.get_w_p_balance())

            return times, powers, balances

    @staticmethod
    def simulate_course(agent, course_data):
        """
        lets given agent run the given course
        :param agent:
        :param course_data:
        :return:
        """

        agent.reset()
        # estimate W' bal history for...
        w_bal_hist = []
        # ... integral agents
        if isinstance(agent, CpIntegralAgentBasis):
            w_bal_hist = agent.estimate_w_p_bal_to_data(course_data)
        # ... differential agent
        elif isinstance(agent, CpDifferentialAgentBasis):
            for tick in course_data:
                agent.set_power(tick)
                agent.perform_one_step()
                w_bal_hist.append(agent.get_w_p_balance())
        # ... hydraulic agent
        elif isinstance(agent, ThreeCompHydAgent):
            for tick in course_data:
                agent.set_power(tick)
                agent.perform_one_step()
                w_bal_hist.append(agent.get_w_p_ratio())

        return w_bal_hist
