# ------------------------------------------------------------------------------------------------ #
# MIT License                                                                                      #
#                                                                                                  #
# Copyright (c) 2020, Microsoft Corporation                                                        #
#                                                                                                  #
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software    #
# and associated documentation files (the "Software"), to deal in the Software without             #
# restriction, including without limitation the rights to use, copy, modify, merge, publish,       #
# distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the    #
# Software is furnished to do so, subject to the following conditions:                             #
#                                                                                                  #
# The above copyright notice and this permission notice shall be included in all copies or         #
# substantial portions of the Software.                                                            #
#                                                                                                  #
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING    #
# BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND       #
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,     #
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,   #
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.          #
# ------------------------------------------------------------------------------------------------ #

from functools import partial

import gym
import jax
import haiku as hk
import numpy as onp

from .._base.test_case import TestCase
from .random_policy import RandomPolicy


env = gym.make('FrozenLakeNonSlippery-v0')


def func_type2(S, is_training):
    batch_norm = hk.BatchNorm(False, False, 0.99)
    seq = hk.Sequential((
        hk.Flatten(),
        hk.Linear(8), jax.nn.relu,
        partial(hk.dropout, hk.next_rng_key(), 0.25 if is_training else 0.),
        partial(batch_norm, is_training=is_training),
        hk.Linear(8), jax.nn.relu,
        hk.Linear(env.action_space.n),
    ))
    return seq(S)


class TestRandomPolicy(TestCase):
    def setUp(self):
        self.env = gym.make('FrozenLakeNonSlippery-v0')

    def tearDown(self):
        del self.env

    def test_call(self):
        pi = RandomPolicy(self.env.action_space)
        s = self.env.reset()
        for t in range(self.env.spec.max_episode_steps):
            a = pi(s)
            s, r, done, info = self.env.step(a)
            if done:
                break

    def test_greedy(self):
        pi = RandomPolicy(self.env.action_space)
        s = self.env.reset()
        for t in range(self.env.spec.max_episode_steps):
            a = pi.mode(s)
            s, r, done, info = self.env.step(a)
            if done:
                break

    def test_dist_params(self):
        pi = RandomPolicy(self.env.action_space)
        s = self.env.observation_space.sample()
        dist_params = pi.dist_params(s)
        print(onp.exp(dist_params['logits']))
        self.assertEqual(dist_params['logits'].shape, (self.env.action_space.n,))
