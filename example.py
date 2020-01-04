from tqdm import tqdm
from time import sleep
for i in tqdm(range(10), desc='outer loop'):
    for j in tqdm(range(1000), desc='inner loop', leave=False):
        sleep(0.001)
        pass
