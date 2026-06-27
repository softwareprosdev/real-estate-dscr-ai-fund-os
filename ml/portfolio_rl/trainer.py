"""
RL trainer using Stable Baselines3 PPO.

PPO is chosen over DQN because:
- The action space is small (5 discrete actions) but the state is continuous
- PPO's clipped objective prevents destructive policy updates
- Easier to tune than SAC for this type of episodic portfolio problem
"""
from __future__ import annotations
import os
from pathlib import Path
from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.callbacks import EvalCallback, CheckpointCallback
from ml.portfolio_rl.environment import DSCRPortfolioEnv


CHECKPOINT_DIR = Path("ml/portfolio_rl/checkpoints")
LOG_DIR = Path("ml/portfolio_rl/logs")


def train(
    deal_generator,
    total_timesteps: int = 500_000,
    n_eval_episodes: int = 10,
    eval_freq: int = 10_000,
) -> PPO:
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    env = DSCRPortfolioEnv(deal_generator=deal_generator)
    check_env(env, warn=True)

    eval_env = DSCRPortfolioEnv(deal_generator=deal_generator)

    checkpoint_cb = CheckpointCallback(
        save_freq=eval_freq,
        save_path=str(CHECKPOINT_DIR),
        name_prefix="dscr_ppo",
    )
    eval_cb = EvalCallback(
        eval_env,
        best_model_save_path=str(CHECKPOINT_DIR / "best"),
        log_path=str(LOG_DIR),
        eval_freq=eval_freq,
        n_eval_episodes=n_eval_episodes,
        deterministic=True,
    )

    model = PPO(
        policy="MlpPolicy",
        env=env,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        gamma=0.95,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.01,
        verbose=1,
        tensorboard_log=str(LOG_DIR),
    )

    model.learn(
        total_timesteps=total_timesteps,
        callback=[checkpoint_cb, eval_cb],
        progress_bar=True,
    )

    model.save(str(CHECKPOINT_DIR / "dscr_ppo_final"))
    return model


def load_model(path: str | None = None) -> PPO | None:
    target = path or str(CHECKPOINT_DIR / "best" / "best_model")
    if not Path(target + ".zip").exists():
        return None
    return PPO.load(target)
