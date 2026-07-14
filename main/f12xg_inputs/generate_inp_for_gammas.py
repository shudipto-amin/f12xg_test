import numpy as np

with open('betas_for_He.tinp', 'r') as inp:

    content = inp.read()

gi = 0.45
gf = 5.00
step = 0.05
gamma_list = np.arange(gi, gf+step/2, step)
gamma_str = ','.join([f"{g:3.2f}" for g in gamma_list])

content = content.replace('__gamma_list__', '['+gamma_str+']')
print(content)
