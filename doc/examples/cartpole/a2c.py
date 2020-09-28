import coax
import gym
import haiku as hk
import jax
import jax.numpy as jnp
import optax
from coax.value_losses import mse


# the name of this script
name = 'a2c'

# the cart-pole MDP
env = gym.make('CartPole-v0')
env = coax.wrappers.TrainMonitor(env, name=name, tensorboard_dir=f"./data/tensorboard/{name}")


def func_pi(S, is_training):
    logits = hk.Sequential((
        hk.Linear(8), jax.nn.relu,
        hk.Linear(8), jax.nn.relu,
        hk.Linear(8), jax.nn.relu,
        hk.Linear(env.action_space.n, w_init=jnp.zeros)
    ))
    return {'logits': logits(S)}


def func_v(S, is_training):
    value = hk.Sequential((
        hk.Linear(8), jax.nn.relu,
        hk.Linear(8), jax.nn.relu,
        hk.Linear(8), jax.nn.relu,
        hk.Linear(1, w_init=jnp.zeros), jnp.ravel
    ))
    return value(S)


# these optimizers collect batches of grads before applying updates
optimizer_v = optax.chain(optax.apply_every(k=32), optax.adam(0.002))
optimizer_pi = optax.chain(optax.apply_every(k=32), optax.adam(0.001))


# value function and its derived policy
v = coax.V(func_v, env)
pi = coax.Policy(func_pi, env)

# experience tracer
tracer = coax.reward_tracing.NStep(n=1, gamma=0.9)

# updaters
vanillapg = coax.policy_objectives.VanillaPG(pi, optimizer=optimizer_pi)
simple_td = coax.td_learning.SimpleTD(v, loss_function=mse, optimizer=optimizer_v)


# train
for ep in range(1000):
    s = env.reset()

    for t in range(env.spec.max_episode_steps):
        a = pi(s)
        s_next, r, done, info = env.step(a)
        if done and (t == env.spec.max_episode_steps - 1):
            r = 1 / (1 - tracer.gamma)

        tracer.add(s, a, r, done)
        while tracer:
            transition_batch = tracer.pop()
            Adv = simple_td.td_error(transition_batch)

            metrics = {}
            metrics.update(vanillapg.update(transition_batch, Adv))
            metrics.update(simple_td.update(transition_batch))
            env.record_metrics(metrics)

        if done:
            break

        s = s_next

    # early stopping
    if env.avg_G > env.spec.reward_threshold:
        break


# run env one more time to render
coax.utils.generate_gif(env, policy=pi.mode, filepath=f"./data/{name}.gif", duration=25)
