"""
Gymnasium-compatible RL environment for DSCR portfolio acquisition.

Key design decisions:
- Episode = one fiscal quarter of deal flow
- Observations = 30-dim flattened state vector (see RLState.to_flat_vector)
- Actions = discrete: BUY, REJECT, HOLD, INCREASE_BID, DECREASE_BID
- Reward = discounted cash flow + appreciation - penalties (see RLReward)
- Terminal: cash depleted, quarter ends, or max properties reached
"""
from __future__ import annotations
import numpy as np
import gymnasium as gym
from gymnasium import spaces
from backend.shared_models.rl_schema import RLAction


ACTION_LIST = [
    RLAction.BUY,
    RLAction.REJECT,
    RLAction.HOLD,
    RLAction.INCREASE_BID,
    RLAction.DECREASE_BID,
]
STATE_DIM = 30


class DSCRPortfolioEnv(gym.Env):
    """
    DSCR real estate portfolio acquisition environment.

    Each step presents one property deal. The agent decides whether to
    acquire, reject, or adjust the bid. Portfolio constraints are enforced.
    """

    metadata = {"render_modes": ["human"]}

    def __init__(
        self,
        deal_generator,
        initial_capital: float = 2_000_000.0,
        max_properties: int = 20,
        episode_length: int = 50,
        zip_exposure_limit: float = 0.30,
        state_exposure_limit: float = 0.50,
        min_dscr: float = 1.20,
    ):
        super().__init__()
        self.deal_generator = deal_generator
        self.initial_capital = initial_capital
        self.max_properties = max_properties
        self.episode_length = episode_length
        self.zip_exposure_limit = zip_exposure_limit
        self.state_exposure_limit = state_exposure_limit
        self.min_dscr = min_dscr

        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(STATE_DIM,), dtype=np.float32
        )
        self.action_space = spaces.Discrete(len(ACTION_LIST))

        self._reset_state()

    def _reset_state(self) -> None:
        self.cash = self.initial_capital
        self.properties: list[dict] = []
        self.step_count = 0
        self.current_deal = None
        self.episode_reward = 0.0
        self.bid_adjustment = 0.0

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self._reset_state()
        self.current_deal = self.deal_generator.next()
        obs = self._get_obs()
        return obs, {}

    def step(self, action: int):
        action_enum = ACTION_LIST[action]
        reward, info = self._apply_action(action_enum)

        self.step_count += 1
        self.episode_reward += reward

        terminated = (
            self.cash < 10_000
            or len(self.properties) >= self.max_properties
            or self.step_count >= self.episode_length
        )

        if not terminated:
            self.current_deal = self.deal_generator.next()
            self.bid_adjustment = 0.0

        obs = self._get_obs()
        return obs, reward, terminated, False, info

    def _apply_action(self, action: RLAction) -> tuple[float, dict]:
        deal = self.current_deal
        if deal is None:
            return 0.0, {"reason": "no_deal"}

        if action == RLAction.REJECT:
            reward = self._rejection_reward(deal)
            info = {"action": "reject", "property_id": deal.get("property_id")}
            return reward, info

        if action == RLAction.INCREASE_BID:
            self.bid_adjustment += deal["purchase_price"] * 0.02
            return 0.0, {"action": "increase_bid"}

        if action == RLAction.DECREASE_BID:
            self.bid_adjustment -= deal["purchase_price"] * 0.02
            return 0.0, {"action": "decrease_bid"}

        if action == RLAction.HOLD:
            return 0.0, {"action": "hold"}

        if action == RLAction.BUY:
            return self._execute_buy(deal)

        return 0.0, {}

    def _execute_buy(self, deal: dict) -> tuple[float, dict]:
        price = deal["purchase_price"] + self.bid_adjustment
        equity = price * (1 - deal.get("ltv", 0.75))

        if equity > self.cash:
            return -0.05, {"action": "buy_rejected", "reason": "insufficient_cash"}

        zip_code = deal.get("zip_code", "00000")
        current_zip_exposure = sum(
            p["equity"] for p in self.properties if p.get("zip_code") == zip_code
        )
        deployed = sum(p["equity"] for p in self.properties)
        total_capital = deployed + self.cash
        if (current_zip_exposure + equity) / total_capital > self.zip_exposure_limit:
            return -0.03, {"action": "buy_rejected", "reason": "zip_concentration_limit"}

        if deal.get("dscr_base", 0) < self.min_dscr:
            return -0.10, {"action": "buy_rejected_dscr", "reason": "dscr_below_threshold"}

        self.cash -= equity
        self.properties.append({
            "property_id": deal.get("property_id"),
            "equity": equity,
            "price": price,
            "zip_code": zip_code,
            "monthly_cash_flow": deal.get("monthly_cash_flow", 0),
            "dscr": deal.get("dscr_base", 1.0),
        })

        annual_cf = deal.get("monthly_cash_flow", 0) * 12
        coc = annual_cf / equity if equity > 0 else 0
        irr_proxy = deal.get("irr_estimate", 0.10)

        reward = (coc * 2.0) + (irr_proxy * 1.5)
        reward *= deal.get("lender_approval_probability", 0.7)
        reward -= (1 - deal.get("financing_viable", True)) * 0.5

        return reward, {"action": "buy", "property_id": deal.get("property_id"), "equity": equity}

    def _rejection_reward(self, deal: dict) -> float:
        if deal.get("dscr_base", 0) < 1.0:
            return 0.02
        if deal.get("dscr_base", 0) < self.min_dscr:
            return 0.01
        return -0.005

    def _get_obs(self) -> np.ndarray:
        if self.current_deal is None:
            return np.zeros(STATE_DIM, dtype=np.float32)
        obs = self.current_deal.get("state_vector", np.zeros(STATE_DIM))
        return np.array(obs, dtype=np.float32)

    def render(self):
        deployed = sum(p["equity"] for p in self.properties)
        print(
            f"Step {self.step_count} | Cash: ${self.cash:,.0f} | "
            f"Properties: {len(self.properties)} | "
            f"Deployed: ${deployed:,.0f} | Episode Reward: {self.episode_reward:.4f}"
        )
