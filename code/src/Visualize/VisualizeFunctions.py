#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Dec  6 15:36:40 2017

@author: bavo
"""
import torch
from torch.autograd import Variable
import matplotlib.pyplot as plt
from scipy.stats import norm
from sklearn.decomposition import PCA as sklearnPCA
import numpy as np
import librosa
import Annote
import pyo

# Perform one run of VAE
def RunVAEOnce(trainloader, VAE_test):
    dataiter = iter(trainloader)
    sample_dict = dataiter.next()
    
    X = sample_dict['image']
    labels = sample_dict['label']
    
    X = Variable(X)
    X = X.float()
    VAE_test.forward(X)
    X_mu = VAE_test.X_mu
    
    X_np = X.data.numpy()
    X_mu_np = X_mu.data.numpy()
    labels_np = labels.numpy()
    return X_np, labels_np, X_mu_np

###############################  Test 1: compare in- and output ###############################
def plotInOut(X_np, X_mu_np, idx):
    image_out = X_mu_np[idx]
    image_in = X_np[idx]
    images = [image_in, image_out]
    
    # Plot
    fig = plt.figure()
    ax1 = fig.add_subplot(211)
    ax1.plot(images[0])
    plt.ylabel('Normalized amplitude')
    plt.title('In- output reconstruction')
    ax2 = fig.add_subplot(212)
    ax2.plot(images[1]) 
    plt.xlabel('Frequency bin')
    plt.ylabel('Normalized amplitude')

# analyse z-space (random z)
def plotRandZ(VAE_test, idx):
    z = Variable(torch.randn(VAE_test.mb_size, VAE_test.encoder.dimZ))*5
    
    VAE_test.decode(z)
    X_mu = VAE_test.X_mu
    X_mu = X_mu.data.numpy()
    
    # Plot
    fig = plt.figure()
    
    ax1 = fig.add_subplot(411)
    plt.title('Random sampling of latent space')
    ax1.axes.get_xaxis().set_visible(False)
    ax1.plot(X_mu[idx])
    
    ax1 = fig.add_subplot(412)
    ax1.axes.get_xaxis().set_visible(False)
    ax1.plot(X_mu[idx+1])
    
    ax1 = fig.add_subplot(413)
    plt.ylabel('Amplitude')
    ax1.axes.get_xaxis().set_visible(False)
    ax1.plot(X_mu[idx+2])
    
    ax1 = fig.add_subplot(414)
    ax1.plot(X_mu[idx+3])
    
    plt.xlabel('Frequency bin')
    
    
def plotLinearZ(VAE_test, frameNb, zdim_y, zdim_x, zdim_xrange, outputfolder):
    for j in range(zdim_xrange):
        VAE_test.eval()
    #    for j in range(VAE_test.decoder.dimZ):
        tensorParamValues = torch.FloatTensor(
                frameNb, VAE_test.decoder.dimZ).zero_()
        for i in range(frameNb):
            tensorParamValues[i][zdim_y] = float(i * 20) / float(frameNb) - 10
            tensorParamValues[i][zdim_x] = float(j * 10) / float(zdim_xrange) - 5
        sample = Variable(tensorParamValues)
        VAE_test.decode(sample)
        image = VAE_test.X_mu.cpu()
        plt.imsave(outputfolder + 'test_z' + str(zdim_x) + str(j) + '.png',\
                   (image.data.view(frameNb, VAE_test.decoder.dimX)).numpy(),\
                   vmin = np.min(image.data.numpy()), vmax=np.max(image.data.numpy()))
    
#    plt.xlabel('Frequency bin')
#    plt.ylabel('z-value')
#    plt.title('Linear variation of one latent space dimension')

# analyse z=space (Guassian mesh)
def CreateZMesh(VAE_test):
    # Create Guassian distribution mesh
    x, y = np.mgrid[0:1:1.0/np.floor(np.sqrt(VAE_test.mb_size)), 0:1:1.0/np.floor(np.sqrt(VAE_test.mb_size))]
    x = norm.ppf(x)
    y = norm.ppf(y) 
    x[0,:]= - 2
    y[:,0] = -2
    x = x.reshape(len(x)**2,)*2
    y = y.reshape(len(y)**2,)*2
    z = np.array([x,y]).T
    if VAE_test.decoder.dimZ > 2:
        # Append zeros for z > 2
        z = np.append(z,np.zeros((len(x),VAE_test.decoder.dimZ - 2)),axis=1)
        z = np.append(z,np.zeros((VAE_test.mb_size - len(x),VAE_test.decoder.dimZ)), axis = 0)
    z = Variable(torch.from_numpy(z).float())
    
    # Decode mesh to images
    VAE_test.decode(z)
    X_mu = VAE_test.X_mu
    samples = X_mu.data.numpy()
    
    # Plot
    fig = plt.figure()
    plt.title('Gaussian mesh sampling of latent space')
    plt.xlim(-4, 4)
    plt.ylim(-4, 4)
    for i in range(0,len(x)):
        ax = fig.add_subplot(np.sqrt(len(x)),np.sqrt(len(x)),i+1)
        ax.plot(samples[i,:])
        ax.set_yticklabels([])
        ax.set_xticklabels([])
#        ax.xaxis.set_ticks_position('none')
#        ax.yaxis.set_ticks_position('none')
        ax.yaxis.set_major_locator(plt.NullLocator())
        ax.xaxis.set_major_formatter(plt.NullFormatter())
    fig.show()

# visualize with PCA
def PlotPCA(VAE_test, trainloader, data_set, PCAdim, factor, nb_labels):
    
    dataiter = iter(trainloader)
    sample_dict = dataiter.next()
    labels = sample_dict['label']
    label_ar = np.zeros((1,labels.shape[1]))  
    z_mu_ar = np.zeros((1,VAE_test.encoder.dimZ))
    
    for i in range(nb_labels/VAE_test.mb_size):
        dataiter = iter(trainloader)
        sample = dataiter.next()
        X = sample['image'].float()
        label = sample['label'].numpy()
        X = Variable(X)
        
        # Actual VAE
        VAE_test.forward(X)
        label_ar = np.append(label_ar,label,axis=0)
    
        z_mu = VAE_test.z_mu
        z_mu = z_mu.data.numpy()
        z_mu_ar = np.append(z_mu_ar, z_mu,axis=0)
    label_ar = np.delete(label_ar,0,axis=0)
    z_mu_ar = np.delete(z_mu_ar,0,axis=0)
    
    sklearn_pca = sklearnPCA(PCAdim)
    PCA_proj = sklearn_pca.fit_transform(z_mu_ar)
    
    fig = plt.figure(figsize=(12, 8))
    ax = fig.subplots()
    x_total = []
    y_total = []    
    lbl_total = []
    lbl_4 = ['Inh.', '# Harm.', 'Q','Filter f']
    lbl_5 = ['Carrier', 'Ratio', 'Index','Q', 'Filter f']

    if labels.shape[1] == 4:
        factors = range(4)
        legend_title = lbl_4[factor]
        factors.remove(factor)
        lbl_size = factors[0]
        lbl_lbl1 = factors[1]
        lbl_lbl2 = factors[2]
    elif labels.shape[1] == 5:
        factors = range(5)
        legend_title = lbl_5[factor]
        factors.remove(factor)
        lbl_size = factors[0]
        lbl_lbl1 = factors[1]
        lbl_lbl2 = factors[2]
        lbl_lbl3 = factors[3]
    else:
        print('Wrong number of labels')
        return
    # Loop over all factor increments to create bool array
    for i in range(20):
        
        bool_ar = label_ar[:,factor] == i
        
        
        color_ar = np.random.random_sample((3,))
        if not len(PCA_proj[bool_ar,0]) == 0:
            x_ar = np.zeros((len(PCA_proj[bool_ar,0]),1))
            y_ar = np.zeros((len(PCA_proj[bool_ar,0]),1))
            s_ar = np.zeros((len(PCA_proj[bool_ar,0]),1))
            lbl_ar = np.chararray(x_ar.shape,itemsize=30)
            
            # Get all points for one increment (one color) and associated label
            for j in range(len(PCA_proj[bool_ar,0])):
                x_ar[j] = PCA_proj[bool_ar, 0][j]
                y_ar[j] = PCA_proj[bool_ar, 1][j]
                
                s_ar[j] = label_ar[j,lbl_size]*20
                if labels.shape[1] == 4:
                    lbl_ar[j] = lbl_4[lbl_lbl1] + ' =' + str(int(label_ar[j,lbl_lbl1])) + ' ' + lbl_4[lbl_lbl2] + ' =' +  str(int(label_ar[j,lbl_lbl2]))
                elif labels.shape[1] == 5:
                    lbl_ar[j] = lbl_5[lbl_lbl1] + ' =' + str(int(label_ar[j,lbl_lbl1])) + ' ' + lbl_5[lbl_lbl2] + ' =' +  str(int(label_ar[j,lbl_lbl2]))  + ' ' + lbl_5[lbl_lbl3] + ' =' +  str(int(label_ar[j,lbl_lbl3]))

            x_ar = x_ar.T.tolist()[0]
            y_ar = y_ar.T.tolist()[0]
            lbl_ar = lbl_ar.T.tolist()[0]
            
            # Plot points and save in total array for labels
            ax.scatter(x_ar, y_ar, c=color_ar, alpha=0.5, s = s_ar, label=str(i))
            x_total = x_total + x_ar
            y_total = y_total + y_ar
            lbl_total = lbl_total + lbl_ar
    
    # Plot scatter and place labels
    af =  Annote.AnnoteFinder(x_total,y_total, lbl_total, ax=ax, xtol = 0.1, ytol = 0.1)
    #fig.canvas.mpl_connect('motion_notify_event', af)
    fig.canvas.mpl_connect('button_press_event', af)
    ax.legend(title = legend_title)
    add_x = np.std(PCA_proj[:,0])/2
    add_y = np.std(PCA_proj[:,1])/2
    ax.set_xlim(min(PCA_proj[:,0])-add_x*4 ,max(PCA_proj[:,0])+add_x*4)
    ax.set_ylim(min(PCA_proj[:,1])-add_y*4,max(PCA_proj[:,1])+add_y*4)
    plt.xlabel('Dim 1 (z)')
    plt.ylabel('Dim 2 (z)')
    plt.title('PCA analysis of ' + data_set + ' dataset with ' + str(labels.shape[1]) + ' factors of variation')
    plt.grid(True)
    
    return sklearn_pca

    
###############################  Test 2: Calculate/visualize loss ###############################
    
# Calculate mean and variance for loss/dataset/factor of variation
def CalculateDatasetLoss(trainloader, VAE_test):
    loss_dataset = np.zeros((len(trainloader.dataset),3))
    dataiter = iter(trainloader)
    sample_dict = dataiter.next()
    labels = sample_dict['label']
    label_ar = np.zeros((1,labels.shape[1]))            
    
    for i, sample in enumerate(trainloader):
        X = sample['image'].float()
        label = sample['label'].numpy()
        X = Variable(X)
        
        # Actual VAE
        VAE_test.forward(X)
        lossVariable, recon, kl = VAE_test.loss(X)
        loss_dataset[i,0] = lossVariable.data[0]
        loss_dataset[i,1] = recon.data[0]
        loss_dataset[i,2] = kl.data[0]
        label_ar = np.append(label_ar,label,axis=0)
    label_ar = np.delete(label_ar,0,axis=0)
    return loss_dataset, label_ar

def BPlotLabelLoss(loss_dataset, label_ar, VAE_test):
    if label_ar.shape[1] == 4:
        label_steps = [10,20,10,10]
        start_step = [0,0,1,1]
    elif label_ar.shape[1] == 5:
        label_steps = [8,7,8,10,10]
        start_step = [1,1,1,1,1]
    else:
        print('no matching VAE dimension')
        return
    
    box_mat = []
    for i in range(label_ar.shape[1]):
        box_vec = np.zeros((label_steps[i],1))
        for j in range(label_steps[i]):
            bool_ar = label_ar[:,i] == j + start_step[i]
            mean = np.mean(loss_dataset[:,0]*bool_ar.T)
            box_vec[j,0] = mean
        box_mat.append(box_vec)
    
    fig = plt.figure(1, figsize=(9, 6))  
    ax1 = fig.add_subplot(111)
    plt.boxplot(box_mat)
    if label_ar.shape[1] == 4:
        ax1.set_title('Loss for 4 variational factors')
    elif label_ar.shape[1] == 5:
        ax1.set_title('Loss for 5 variational factors')
    ax1.set_ylabel('Loss')
    if label_ar.shape[1] == 4:
        ax1.set_xticklabels(['Inharmonicity', '# Harmonics', 'Filter Q', 'Filter freq.'])
    elif label_ar.shape[1] == 5:
        ax1.set_xticklabels(['Carrier', 'Ratio', 'Index', 'Filter Q', 'Filter freq.'])
    ax1.get_xaxis().tick_bottom()
    ax1.get_yaxis().tick_left()
    #ax1.set_xlim(0.5, 4)
    #ax1.set_ylim(-1, 1)    
    plt.show()

# plot loss evolution
def plotLoss(VAE_test):
#    loss_vector = np.load(model_folder + data_set + '_' + data_name + str(Z_dim) + 'loss_.npy')
    recon = np.asarray(VAE_test.recon_loss)
    regul = np.asarray(VAE_test.regul_loss)
    loss_vector = np.asarray((recon+regul, recon, regul)).T
    fig, ax = plt.subplots()
    x_axis = range(0,len(loss_vector))
    ax.plot(x_axis, loss_vector[0:,0], 'k--', label='Total loss')
    ax.plot(x_axis, loss_vector[0:,1], 'k:', label='Reconstruction loss')
    ax.plot(x_axis, loss_vector[0:,2], 'k', label='Kull/Leib loss')
    ax.legend(loc='upper center', shadow=True)
    
    plt.xlabel('Epoch')
    plt.ylabel('Loss value')
    plt.title('Loss evolution during VAE training')
    
def plotLoss_depreciated(model_folder, data_set, data_name, Z_dim):
    loss_vector = np.load(model_folder + data_set + '_' + data_name + str(Z_dim) + 'loss_.npy')
    fig, ax = plt.subplots()
    x_axis = range(0,len(loss_vector))
    ax.plot(x_axis, loss_vector[0:,0], 'k--', label='Total loss')
    ax.plot(x_axis, loss_vector[0:,1], 'k:', label='Reconstruction loss')
    ax.plot(x_axis, loss_vector[0:,2], 'k', label='Kull/Leib loss')
    ax.legend(loc='upper center', shadow=True)

# ###############################  Test 3:  Signal Reconstruction and granular synth ###############################
def MoveAudio(data_folder, dataname, labels_np, idx):
    label_in = labels_np[idx]
    
    if len(label_in) == 4:
        filename = 'set1_' + str(int(label_in[0])) + '_' + str(int(label_in[1])) + '_' + str(int(label_in[2])) + '_' + str(int(label_in[3])) + '_.wav'
    elif len(label_in) == 5:
        filename = 'set1_' + str(int(label_in[0])) + '_' + str(int(label_in[1])) + '_' + str(int(label_in[2])) + '_' + str(int(label_in[3])) + '_' + str(int(label_in[4])) + '_.wav'
    
    if dataname == 'dataset2BVK.npz':
        folder = 'toy_dataset_2'
    elif dataname == 'dataset3BVK.npz':
        folder = 'toy_dataset_3'
    
    y, sr = librosa.load(data_folder + folder + '/' + filename, sr=None)
    output_name = 'test_stft'
    librosa.output.write_wav(output_name + '.wav', y, 44100) 
    
def SpecPhaseToAudio(X_mu_np, idx, nbFrames, outputpath = ''):
    Nfft = 4096
    spectrum_in = X_mu_np[idx,1025:2050]
    phase_in = X_mu_np[idx,0:1025]
    S = np.repeat(spectrum_in[np.newaxis].T,nbFrames,axis=1)
    phase_in = np.repeat(phase_in[np.newaxis].T,nbFrames,axis=1)
    S = np.append(S, np.zeros((Nfft/2-S.shape[0]+1,nbFrames)),axis=0)
    x = griffLim_stft(S, phase_in)
    output_name = 'ReconAudio_'
    librosa.output.write_wav(outputpath + output_name + 'gl.wav', x, 44100)

def SpecToAudio(X_mu_np, idx, nbFrames, outputpath = ''):
    Nfft = 4096
    S = np.repeat(X_mu_np[idx,:][np.newaxis].T,nbFrames,axis=1)
    S = np.append(S, np.zeros((Nfft/2-S.shape[0]+1,nbFrames)),axis=0)
    x = griffLim_stft(S)*300
    output_name = 'ReconAudio_'
    librosa.output.write_wav(outputpath + output_name + 'gl.wav', x, 44100)
    
def griffLim_stft(S, Phase = 0): 
    Nfft = S.shape[0]*2 - 2
    S = np.log1p(np.abs(S))  
    a = np.zeros_like(S)
    a = np.exp(S) - 1
    if not type(Phase) == int:
        Phase = np.append(Phase, np.random.random_sample((Nfft/2-Phase.shape[0]+1,Phase.shape[1])),axis=0)
        p = Phase
    else:
        p = 2*np.pi*np.random.random_sample(a.shape) -np.pi
    for i in xrange(250):
        S = a*np.exp(1j*p)
        x = librosa.istft(S)
        spec = librosa.stft(x, n_fft = Nfft)
        p = np.angle(spec)
    return x

def MDCTToAudio(X_mu_np, idx, nbFrames, outputpath = ''):
    x = X_mu_np[idx,:]
    y = imdct4(x)
    temp = np.zeros((nbFrames*len(y)/2))
    for i in range(nbFrames-1):
        temp[i*len(y)/2:(i+2)*len(y)/2] += y
    output_name = 'ReconAudio_'
    librosa.output.write_wav(outputpath + output_name + 'MDCT.wav', temp, 44100)
    
def imdct4(x):
    N = x.shape[0]
    if N%2 != 0:
        raise ValueError("iMDCT4 only defined for even-length vectors.")
    M = N // 2
    N2 = N*2
    
    t = np.arange(0,M)
    w = np.exp(-1j*2*np.pi*(t + 1./8.) / N2)
    c = np.take(x,2*t) + 1j * np.take(x,N-2*t-1)
    c = 0.5 * w * c
    c = np.fft.fft(c,M)
    c = ((8 / np.sqrt(N2))*w)*c
    
    rot = np.zeros(N2)
    
    rot[2*t] = np.real(c[t])
    rot[N+2*t] = np.imag(c[t])
    
    t = np.arange(1,N2,2)
    rot[t] = -rot[N2-t-1]
    
    t = np.arange(0,3*M)
    y = np.zeros(N2)
    y[t] = rot[t+M]
    t = np.arange(3*M,N2)
    y[t] = -rot[t-3*M]
    return y

def SpecToGranulator(X_mu_np, idx):
    Nfft = 4096
    S = X_mu_np[idx,:]
    S = np.append(S[np.newaxis].T, np.zeros((Nfft/2-S.shape[0]+1,1)),axis=0)
    x = np.fft.irfft(S, n=Nfft)
    s = pyo.Server(sr=44100, duplex = 0)
    s.boot()
    s.start()
    tab = pyo.DataTable(size=1024, init=x.tolist())
    tab.view()
    env = pyo.HannTable()
    pos = pyo.Phasor(1024/44100, 0, 1024)
    dur = pyo.Noise(.001, .1)
    g = pyo.Granulator(tab, env, 1, pos, dur, 24, mul=1).out()
    s.gui(locals(),exit=True)

    