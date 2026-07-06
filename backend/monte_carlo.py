import numpy as np
from concurrent.futures import ProcessPoolExecutor
import os

def _worker(s0,k,r,sigma,t,opt,n,seed):
    np.random.seed(seed)
    z=np.random.standard_normal(n)
    st=s0*np.exp((r-0.5*sigma**2)*t+sigma*np.sqrt(t)*z)
    payoff=np.maximum(st-k,0) if opt=="call" else np.maximum(k-st,0)
    return payoff.sum()

def monte_carlo_option_price_parallel(s0,k,r,sigma,t,option_type,simulations=100000,workers=None):
    workers=workers or max(os.cpu_count()-1,1)
    chunk=simulations//workers
    rem=simulations%workers
    total=0
    with ProcessPoolExecutor(max_workers=workers) as ex:
        fut=[]
        for i in range(workers):
            n=chunk+(rem if i==workers-1 else 0)
            fut.append(ex.submit(_worker,s0,k,r,sigma,t,option_type,n,i+1))
        for f in fut:
            total+=f.result()
    return np.exp(-r*t)*(total/simulations)
