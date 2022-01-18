import logging

from threecomphyd.agents.three_comp_hyd_agent import ThreeCompHydAgent
from pypermod.agents.wbal_agents.wbal_ode_agent_linear import CpODEAgentBasisLinear
from pypermod.agents.wbal_agents.wbal_int_agent import WbalIntAgent


class SimulatorBasis:
    """
    Contains convenience functions to run simulations with performance modelling agents. Example simulations are
    time-to-exhaustion (TTE) or recovery estimations according with the WB1 -> RB -> WB2 protocol
    """
    # the maximal number of steps for a single simulation run
    step_limit = 5000

    @staticmethod
    def simulate_tte(agent, p_work):
        """
        estimates time to exhaustion for given agent at given intensity
        :param agent:
        :param p_work:
        :return:
        """

        agent.reset()

        # ... integral agents
        if isinstance(agent, WbalIntAgent):
            w_bal_hist = agent.get_expenditure_dynamics(p_work)
            return w_bal_hist

        # ... differential agent
        elif isinstance(agent, CpODEAgentBasisLinear):
            agent.set_power(p_work)
            step = 0
            w_bal_hist = []
            while not agent.is_exhausted() and step < SimulatorBasis.step_limit:
                agent.perform_one_step()
                w_bal_hist.append(agent.get_w_p_balance())
                step += 1
            if not agent.is_exhausted():
                raise UserWarning("Exhaustion not reached")
            return w_bal_hist
        # ... hydraulic agent
        elif isinstance(agent, ThreeCompHydAgent):
            agent.set_power(p_work)
            step = 0
            w_bal_hist = []
            while not agent.is_exhausted() and step < SimulatorBasis.step_limit:
                agent.perform_one_step()
                w_bal_hist.append(agent.get_w_p_ratio())
                step += 1
            if not agent.is_exhausted():
                raise UserWarning("Exhaustion not reached")
            return w_bal_hist
        # unknown type warning
        raise UserWarning("No procedure implemented for agent type {}".format(agent))

    @staticmethod
    def get_recovery_ratio_wb1_wb2(agent, p_work, p_rec, t_rec):
        """
        Returns recovery ratio of given agent according to WB1 -> RB -> WB2 protocol.
        Recovery ratio estimations for given exp, rec intensity and time
        :param agent:
        :param p_work: work bout intensity
        :param p_rec: recovery bout intensity
        :param t_rec: recovery bout duration
        :return: ratio in percent
        """

        agent.reset()
        hz = agent.hz

        # The handling agent types
        if isinstance(agent, WbalIntAgent):
            dcp = agent.cp - p_rec
            # simulate Caen trials with defined DPC
            c_exp_bal = agent.get_expenditure_dynamics(p_exp=p_work, dcp=dcp)

            # setup course according to found TTE
            caen_course = [p_work] * len(c_exp_bal) + [p_rec] * t_rec + [p_work] * len(c_exp_bal)
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
            agent.set_power(p_work)
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
            agent.set_power(p_work)
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
