import coax
import gym
import jax
import jax.numpy as jnp
import haiku as hk
import optax


# the MDP
env = gym.make('FrozenLakeNonSlippery-v0')
env = coax.wrappers.TrainMonitor(env)


def func(S, A, is_training):
    value = hk.Sequential((hk.Flatten(), hk.Linear(1, w_init=jnp.zeros), jnp.ravel))
    X = jax.vmap(jnp.kron)(S, A)  # s and A are one-hot encoded
    return value(X)


# function approximator
q = coax.Q(func, env)
pi = coax.BoltzmannPolicy(q, temperature=0.1)


# experience tracer
tracer = coax.reward_tracing.NStep(n=1, gamma=0.9)


# updater
qlearning = coax.td_learning.QLearning(q, optimizer=optax.adam(0.02))


# train
for ep in range(500):
    s = env.reset()

    for t in range(env.spec.max_episode_steps):
        a = pi(s)
        s_next, r, done, info = env.step(a)

        # small incentive to keep moving
        if jnp.array_equal(s_next, s):
            r = -0.01

        # update
        tracer.add(s, a, r, done)
        while tracer:
            transition_batch = tracer.pop()
            qlearning.update(transition_batch)

        if done:
            break

        s = s_next


# run env one more time to render
s = env.reset()
env.render()

for t in range(env.spec.max_episode_steps):

    # print individual state-action values
    for i, q_ in enumerate(q(s)):
        print("  q(s,{:s}) = {:.3f}".format('LDRU'[i], q_))

    a = pi.mode(s)
    s, r, done, info = env.step(a)

    env.render()

    if done:
        break
