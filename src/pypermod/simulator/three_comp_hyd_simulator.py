import logging
import numpy as np

from pypermod.agents.hyd_agents.three_comp_hyd_agent import ThreeCompHydAgent
import matplotlib.pyplot as plt


class ThreeCompHydSimulator:
    """
    Tailored to the ThreeComponentHydraulic model, this class offers functions to simulate training sessions,
    TTE tests, and recovery estimation protocols
    """

    @staticmethod
    def tte(agent: ThreeCompHydAgent, p_work: float, start_h: float = 0,
            start_g: float = 0, t_max: float = 5000, step_function=None) -> float:
        """
        simulates a standard time to exhaustion test
        :param agent: hydraulic agent
        :param p_work: constant expenditure intensity for TTE
        :param start_h: fill level of LF at start
        :param start_g: fill level of LS at start
        :param t_max: maximal time in seconds until warning "exhaustion not reached" is raised
        :param step_function: function of agent to estimate one time step. Default is perform_one_step.
        :return: time to exhaustion in seconds
        """
        agent.reset()
        agent.set_h(start_h)
        agent.set_g(start_g)

        step_limit = t_max * agent.hz

        if step_function is None:
            step_function = agent.perform_one_step

        # Exhaust...
        agent.set_power(p_work)
        steps = 0
        while not agent.is_exhausted() and steps < step_limit:
            step_function()
            steps += 1
        tte = agent.get_time()

        if not agent.is_exhausted():
            raise UserWarning("exhaustion not reached!")

        return tte

    @staticmethod
    def get_recovery_ratio_wb1_wb2(agent: ThreeCompHydAgent, p_work: float, p_rec: float,
                                   t_rec: float, start_h: float = 0, start_g: float = 0,
                                   t_max: float = 5000, step_function=None) -> float:
        """
        Returns recovery ratio of given agent according to WB1 -> RB -> WB2 protocol.
        Recovery ratio estimations for given exp, rec intensity and time
        :param agent: three component hydraulic agent to use
        :param p_work: work bout intensity
        :param p_rec: recovery bout intensity
        :param t_rec: recovery bout duration
        :param start_h: fill level of LF at start
        :param start_g: fill level of LS at start
        :param t_max: maximal time in seconds until warning "exhaustion not reached" is raised
        :param step_function: function of agent to estimate one time step. Default is perform_one_step.
        :return: ratio in percent
        """

        hz = agent.hz
        agent.reset()
        agent.set_h(start_h)
        agent.set_g(start_g)

        step_limit = t_max * hz

        if step_function is None:
            step_function = agent.perform_one_step

        # WB1 Exhaust...
        agent.set_power(p_work)
        steps = 0
        while not agent.is_exhausted() and steps < step_limit:
            step_function()
            steps += 1
        wb1_t = agent.get_time()

        if not agent.is_exhausted():
            raise UserWarning("exhaustion not reached!")

        # Recover...
        agent.set_power(p_rec)
        for _ in range(0, int(round(t_rec * hz))):
            step_function()
        rec_t = agent.get_time()

        # WB2 Exhaust...
        agent.set_power(p_work)
        steps = 0
        while not agent.is_exhausted() and steps < step_limit:
            step_function()
            steps += 1
        wb2_t = agent.get_time()

        # return ratio of times as recovery ratio
        return ((wb2_t - rec_t) / wb1_t) * 100.0

    @staticmethod
    def simulate_course_detail(agent: ThreeCompHydAgent, powers,
                               step_function=None, plot: bool = False):
        """
        simulates a whole course with given agent
        :param agent:
        :param powers: list or array
        :param plot: displays a plot of some of the state variables over time
        :param step_function: function of agent to estimate one time step. Default is perform_one_step.
        :return all state variables throughout for every
        time step of the course [h, g, lf, ls, p_u, p_l, m_flow, w_p_bal]. Pos 0 is time step 1.
        """

        agent.reset()
        h, g, lf, ls, p_u, p_l, m_flow, w_p_bal = [], [], [], [], [], [], [], []

        if step_function is None:
            step_function = agent.perform_one_step

        # let the agent simulate the list of power demands
        for step in powers:
            # we don't include values of time step 0
            # perform current power step
            agent.set_power(step)
            step_function()
            # ... then collect observed values
            h.append(agent.get_h())
            g.append(agent.get_g())
            lf.append(agent.get_fill_lf())
            ls.append(agent.get_fill_ls())
            p_u.append(agent.get_p_u())
            p_l.append(agent.get_p_l())
            m_flow.append(agent.get_m_flow())
            w_p_bal.append(agent.get_w_p_ratio())

        # an investigation and debug plot if you want to
        if plot is True:
            ThreeCompHydSimulator.plot_dynamics(t=np.arange(len(powers)), p=powers,
                                                lf=lf, ls=ls, p_u=p_u, p_l=p_l)

        # return parameters
        return h, g, lf, ls, p_u, p_l, m_flow, w_p_bal

    @staticmethod
    def tte_detail(agent: ThreeCompHydAgent, p_work: float, start_h: float = 0,
                   start_g: float = 0, t_max: float = 5000, step_function=None,
                   plot: bool = False):
        """
        simulates a standard time to exhaustion test and collects all state variables of the hydraulic agent in
        every time step.
        :param agent: hydraulic agent
        :param p_work: constant expenditure intensity for TTE
        :param start_h: fill level of LF at start
        :param start_g: fill level of LS at start
        :param t_max: maximal time in seconds until warning "exhaustion not reached" is raised
        :param step_function: function of agent to estimate one time step. Default is perform_one_step.
        :param plot: whether state variables over time should be plotted
        :return: all state variables all state variables throughout for every
        time step of the TTE [h, g, lf, ls, p_u, p_l, m_flow, w_p_bal]. Pos 0 is time step 1.
        """

        agent.reset()
        agent.set_h(start_h)
        agent.set_g(start_g)
        step_limit = t_max * agent.hz

        if step_function is None:
            step_function = agent.perform_one_step

        # all state variables are logged
        t, ps = [], []
        lf, ls, h, g, p_u, p_l, m_flow, w_p_bal = [], [], [], [], [], [], [], []

        steps = 0
        agent.set_power(p_work)

        # perform steps until agent is exhausted or step limit is reached
        while not agent.is_exhausted() and steps < step_limit:
            # we don't include values of time step 0
            # perform current power step
            step_function()
            steps += 1
            # ... then collect observed values
            t.append(agent.get_time())
            ps.append(agent.get_power())
            h.append(agent.get_h())
            g.append(agent.get_g())
            lf.append(agent.get_fill_lf())
            ls.append(agent.get_fill_ls())
            p_u.append(agent.get_p_u())
            p_l.append(agent.get_p_l())
            m_flow.append(agent.get_m_flow())
            w_p_bal.append(agent.get_w_p_ratio())

        # a investigation and debug plot if you want to
        if plot is True:
            ThreeCompHydSimulator.plot_dynamics(t=t, p=ps, lf=lf, ls=ls, p_u=p_u, p_l=p_l)

        # return parameters
        return h, g, h, g, p_u, p_l, m_flow, w_p_bal

    @staticmethod
    def tte_detail_with_recovery(agent: ThreeCompHydAgent, p_work, p_rec, plot=False):
        """
        The time the agent takes till exhaustion at given power and time till recovery
        :param agent: agent instance to use
        :param p_work: expenditure intensity
        :param p_rec: recovery intensity
        :param plot: displays a plot of some of the state variables over time
        :returns: tte, ttr
        """

        agent.reset()
        t, p, lf, ls, p_u, p_l, m_flow = [], [], [], [], [], [], []

        # perform steps until agent is exhausted
        logging.info("start exhaustion")
        agent.set_power(p_work)
        steps = 0
        while agent.is_exhausted() is False and steps < 10000:
            t.append(agent.get_time())
            p.append(agent.perform_one_step())
            lf.append(agent.get_fill_lf())
            ls.append(agent.get_fill_ls() * agent.height_ls + agent.theta)
            p_u.append(agent.get_p_u())
            p_l.append(agent.get_p_l())
            m_flow.append(agent.get_m_flow())
            steps += 1
        # save time
        tte = agent.get_time()

        # add recovery at 0
        logging.info("start recovery")
        agent.set_power(p_rec)
        steps = 0
        while agent.is_equilibrium() is False and steps < 20000:
            t.append(agent.get_time())
            p.append(agent.perform_one_step())
            lf.append(agent.get_fill_lf())
            ls.append(agent.get_fill_ls() * agent.height_ls + agent.theta)
            p_u.append(agent.get_p_u())
            p_l.append(agent.get_p_l())
            m_flow.append(agent.get_m_flow())
            steps += 1
        # save recovery time
        ttr = agent.get_time() - tte

        # plot the parameter overview if required
        if plot is True:
            ThreeCompHydSimulator.plot_dynamics(t, p, lf, ls, p_u, p_l)

        # return time till exhaustion and time till recovery
        return tte, ttr

    @staticmethod
    def plot_dynamics(t, p, lf, ls, p_u, p_l):
        """
        Debugging plots for state parameters
        """

        # set up plot
        fig = plt.figure(figsize=(12, 5))
        ax = fig.add_subplot(1, 1, 1)

        # plot liquid flows
        ax.plot(t, p, color='tab:green', label="power")
        ax.plot(t, p_u, color='tab:cyan', label="flow from U")
        ax.plot(t, p_l, color='tab:red', label="flow from LS to LF")

        # plot tank fill levels
        ax2 = ax.twinx()
        ax2.plot(t, lf, color='tab:orange', label="fill level LF", linestyle="--")
        ax2.plot(t, ls, color='tab:red', label="fill level LS", linestyle="--")

        # label plot
        ax.set_xlabel("time (seconds)")
        ax.set_ylabel("flow and power in Watts")
        ax2.set_ylabel("fill level")

        # legends
        ax.legend(loc=1)
        ax2.legend(loc=4)

        # formant plot
        locs, labels = plt.xticks()
        plt.setp(labels, rotation=-45)
        plt.tight_layout()
        plt.show()
