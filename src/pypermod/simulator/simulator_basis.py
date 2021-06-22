import logging

from threecomphyd.agents.three_comp_hyd_agent import ThreeCompHydAgent
from pypermod.agents.wbal_agents.wbal_ode_agent_linear import CpODEAgentBasisLinear
from pypermod.agents.wbal_agents.wbal_int_agent import WbalIntAgent


class SimulatorBasis:
    """
    Contains convenience functions to run simulations with performance modelling agents. Exemplary simulations are
    time-to-exhaustion (TTE) or recovery estimations according to Caen et al. or Sreedhara.
    """
    # the maximal number of steps for a single simulation run
    step_limit = 5000

    @staticmethod
    def simulate_tte(agent, p_exp):
        """
        estimates time to exhaustion for given agent at given intensity
        :param agent:
        :param p_exp:
        :return:
        """

        agent.reset()

        # ... integral agents
        if isinstance(agent, WbalIntAgent):
            w_bal_hist = agent.get_expenditure_dynamics(p_exp)
            return w_bal_hist

        # ... differential agent
        elif isinstance(agent, CpODEAgentBasisLinear):
            agent.set_power(p_exp)
            step = 0
            w_bal_hist = []
            while agent.is_exhausted() is False and step < SimulatorBasis.step_limit:
                agent.perform_one_step()
                w_bal_hist.append(agent.get_w_p_balance())
                step += 1
            if agent.is_exhausted() is False:
                raise UserWarning("Exhaustion not reached")
            return w_bal_hist
        # ... hydraulic agent
        elif isinstance(agent, ThreeCompHydAgent):
            agent.set_power(p_exp)
            step = 0
            w_bal_hist = []
            while agent.is_exhausted() is False and step < SimulatorBasis.step_limit:
                agent.perform_one_step()
                w_bal_hist.append(agent.get_w_p_ratio())
                step += 1
            if agent.is_exhausted() is False:
                raise UserWarning("Exhaustion not reached")
            return w_bal_hist
        # unknown type warning
        raise UserWarning("No procedure implemented for agent type {}".format(agent))

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
        if isinstance(agent, WbalIntAgent):
            dcp = agent.cp - p_rec
            # simulate Caen trials with defined DPC
            c_exp_bal = agent.get_expenditure_dynamics(p_exp=p_exp, dcp=dcp)

            # setup course according to found TTE
            caen_course = [p_exp] * len(c_exp_bal) + [p_rec] * t_rec + [p_exp] * len(c_exp_bal)
            # get W'bal history
            caen_bal = SimulatorBasis.simulate_course(agent, caen_course)

            # look for the time of exhaustion in the second exercise bout
            found_i = 0
            for i in range(len(c_exp_bal) + t_rec, len(caen_bal)):
                if caen_bal[i] <= 0:
                    found_i = i - (len(c_exp_bal) + t_rec) + 1  # plus 1 because the time step 0 is reached is included
                    break

            # Time of WB2 divided by time of WB1 is the ratio of recovery
            ratio = (found_i / len(c_exp_bal)) * 100.0
            return ratio

        elif isinstance(agent, CpODEAgentBasisLinear) or isinstance(agent, ThreeCompHydAgent):
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
        if isinstance(agent, WbalIntAgent):
            data = [p_exp] * round(t_exp / 2) + [p_rec] * round(t_rec) + [p_exp] * round(t_exp * 1.5)
            w_bal_hist = agent.estimate_w_p_bal_to_data(data)
            t3 = w_bal_hist.index(0)  # time point of exhaustion
            # the equation to estimate recovery from ttes of both bouts
            return ((round(t_exp / 2) + (float(t3) - (round(t_exp / 2) + t_rec)) - t_exp) / t_exp) * 100.0

        elif isinstance(agent, CpODEAgentBasisLinear) or isinstance(agent, ThreeCompHydAgent):
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
    def simulate_course(agent, course_data):
        """
        lets given agent run the given course
        :param agent:
        :param course_data: Expected as a list of intensities in Watts
        :return:
        """

        agent.reset()
        # estimate W' bal history for...
        w_bal_hist = []
        # ... integral agents
        if isinstance(agent, WbalIntAgent):
            w_bal_hist = agent.estimate_w_p_bal_to_data(course_data)
        # ... differential agent
        elif isinstance(agent, CpODEAgentBasisLinear):
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
