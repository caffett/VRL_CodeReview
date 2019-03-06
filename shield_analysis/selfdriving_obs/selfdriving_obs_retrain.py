# -*- coding: utf-8 -*-
# -------------------------------
# Author: Zikang Xiong
# Email: zikangxiong@gmail.com
# Date:   2018-11-06 12:23:39
# Last Modified by:   Zikang Xiong
# Last Modified time: 2019-02-13 00:13:42
# -------------------------------
import sys
sys.path.append("../")

from main import *
from shield import Shield
from Environment import Environment

from DDPG import *

from shield_analysis.retrain_nn_and_shield import retrain_nn_and_shield
from shield_analysis.log_scan import read_scan

# Show that there is an invariant that can prove the policy safe
def selfdrive(learning_method, number_of_rollouts, simulation_steps, learning_eposides, critic_structure, actor_structure, train_dir, K=None):
  A = np.matrix([
    [ 0., 0., 1., 0.],
    [ 0., 0., 0., 1.],
    [ 0., 0., -1.2, .1],
    [ 0., 0., .1, -1.2]
    ])
  B = np.matrix([
    [0,0],[0,0],[1,0],[0,1]
    ])

  #intial state space
  s_min = np.array([[-7],[-7],[0],[0]])
  s_max = np.array([[-6],[-8],[0],[0]])

  u_min = np.array([[-1], [-1]])
  u_max = np.array([[ 1], [ 1]])

  x_min = np.array([[[-3.1], [-3.1], [np.NINF], [np.NINF]]])
  x_max = np.array([[[-2.9], [-2.9], [np.inf], [np.inf]]])

  d, p = B.shape

  Q = np.zeros((d, d), float)
  np.fill_diagonal(Q, 1)

  R = np.zeros((p,p), float)
  np.fill_diagonal(R, .005)

  # Use sheild to directly learn a linear controller
  env = Environment(A, B, u_min, u_max, s_min, s_max, x_min, x_max, Q, R, continuous=True, unsafe=True, bad_reward=-2000)

  args = { 'actor_lr': 0.0001,
       'critic_lr': 0.001,
       'actor_structure': actor_structure,
       'critic_structure': critic_structure, 
       'buffer_size': 1000000,
       'gamma': 0.99,
       'max_episode_len': 1000,
       'max_episodes': learning_eposides,
       'minibatch_size': 64,
       'random_seed': 653,
       'tau': 0.005,
       'model_path': train_dir+"model.chkp",
       'enable_test': False, 
       'test_episodes': 1000,
       'test_episodes_len': 5000}
  actor =  DDPG(env, args=args)

  model_path = os.path.split(args['model_path'])[0]+'/'
  linear_func_model_name = 'K.model'
  model_path = model_path+linear_func_model_name+'.npy'

  def rewardf(x, Q, u, R):
    return np.matrix([[env.reward(x, u)]])

  shield = Shield(env, actor, model_path=model_path, force_learning=False)
  shield.train_shield(learning_method, number_of_rollouts, simulation_steps, rewardf=rewardf, explore_mag=1.0, step_size=1.0)
  K = shield.K_list[0]
  shield_state_list = read_scan("selfdriving_obs/selfdriving_obs.log_ret.pkl")
  retrain_nn_and_shield(actor, K, shield_state_list)

  actor.sess.close()

if __name__ == "__main__":

  selfdrive("random_search", 100, 2000, 0, [64, 64], [64, 64], "selfdriving_obs/retrain/64646464/")