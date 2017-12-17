# -*- coding: utf-8 -*-
"""
Created on Sun Nov 26 14:10:26 2017

Script to create toy data-set 1 with six latent space factors
1. Pitch =  70 + exp(i), with i = [0,10,0.5]
2. Harmonicity = sum(sin((2n+j)*f*i), j = [0,1,0.1]
3. # Partials k
4. Noisiness: sig = alpha*sin() + beta*noise()
5. Filter (Q)
6. Filter (f)

@author: bavo
"""
import pyo
import numpy as np
import os

# path to your sound folder
folder_path = "/home/bavo/Documents/ATIAM/4_Informatique/MachineLearning_Project/2_VAE_dataset/"
#folder_path = '/media/bavo/1E84369D843676FD/Users/bavov/Documents/ATIAM/4_Informatique/MachineLearning_Project/Datasets/training_2/'

# create it if it does not exist
if not os.path.isdir(folder_path):
    os.mkdir(folder_path)

# Spectrogram parameters
fft_size = 2048
hop_length = fft_size * 3/4

# Output .npz parameters
imgs_stack = np.zeros([1025,1])
labels_stack = np.zeros([3,121000])
i = 0

# Server parameters
sr = 44100
f0 = 110

# Start server
s = pyo.Server(sr=44100)

for j in np.arange(0,1,0.025):
    freq_ar = [f0]
    for k in np.arange(1,41,1):
        freq_new =  (k + j)*f0
        freq_ar.append(freq_new)
    for Q in np.arange(1,11,0.05):
        for filter_f in np.arange(1,21,0.5):                   
            # set server parameters
            s.boot()
            s.start()
            m1 = pyo.DataTable(size = 2048)
            
            # Create sound
            sin_sig = pyo.Sine(freq=freq_ar, mul = 1)
            sig_filtered = pyo.ButBP(sin_sig, freq = float(filter_f*sr/(2*100)), q = float(Q))
            
            # start the render
            rec = pyo.TablePut(sig_filtered, table = m1).play()
            pyo.time.sleep(0.1)
            samps = m1.getTable()
            y = np.asarray(samps) 
            # cleanup
            s.shutdown()
            
            # Create spectrum
            D = np.fft.fft(y,fft_size)[0:fft_size/2+1]
            log_D = 20*np.log10(np.abs(D)**2)               
            
            # Store in numpy array
            imgs_stack = np.dstack((imgs_stack, log_D[:][np.newaxis].T))
            labels_stack[0][i] = j
            labels_stack[1][i] = Q 
            labels_stack[2][i] = filter_f
            
            i = i + 1
                    
imgs_stack = np.delete(imgs_stack,0,2)
toy_dataset_dict = {'images': imgs_stack, 'labels': labels_stack, 'frequencies':freq_ar}
np.savez(folder_path + 'toy_dataset_2_BVK.npz', **toy_dataset_dict)

                    
                    