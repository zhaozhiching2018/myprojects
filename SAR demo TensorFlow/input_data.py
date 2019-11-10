#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 16 16:31:19 2017

@author: didizhang
"""

import tensorflow as tf
import numpy as np
import os

#%%
train_dir = 'data/train/17_DEG/'
val_dir = 'data/test/15_DEG/'
#返回存放文件的路径及对应标签
def get_files(file_dir):
    '''
    Args:
        file_dir: file directory
    Returns:
        list of images and labels
    '''
    BMP2 = []
    label_BMP2 = []
    BTR70 = []
    label_BTR70 = []
    T72 = []
    label_T72 = []
    S2S1=[]
    label_S2S1=[]
    BRDM_2=[]
    label_BRDM_2=[]
    D7=[]
    label_D7=[]
    SLICY=[]
    label_SLICY=[]
    T62=[]
    label_T62=[]
    ZIL131=[]
    label_ZIL131=[]
    ZSU_23_4=[]
    label_ZSU_23_4=[]    
  
    for file in os.listdir(file_dir):
        name = file.split(sep='.') 
        if name[0]=='2S1':
            S2S1.append(file_dir + file)
            label_S2S1.append(0)
        if name[0]=='BRDM_2':
            BRDM_2.append(file_dir + file) 
            label_BRDM_2.append(1)
        if name[0]=='D7':
            D7.append(file_dir + file)
            label_D7.append(2)
        
        if name[0]=='T62':
            T62.append(file_dir + file) 
            label_T62.append(3)
        if name[0]=='ZIL131':
            ZIL131.append(file_dir + file)
            label_ZIL131.append(4)
        if name[0]=='ZSU_23_4':
            ZSU_23_4.append(file_dir + file)
            label_ZSU_23_4.append(5)
        if name[0]=='1SLICY':
            SLICY.append(file_dir + file)
            label_SLICY.append(6)    
    '''
    namei=0
    for dicname in os.listdir(file_dir):
        for file in os.listdir(file_dir+dicname): 
            BMP2.append(file_dir+dicname +'/'+ file)
            label_BMP2.append(namei)
        namei=namei+1
  
    '''
    #print(BMP2)
    #print(label_BMP2)
    print('There are %d BMP2\nThere are %d BTR70\nThere are %d T72' %(len(BMP2), len(BTR70),len(T72)))
    image_list = np.hstack((BMP2, BTR70, T72,S2S1,BRDM_2,D7,SLICY,T62,ZIL131,ZSU_23_4))
    label_list = np.hstack((label_BMP2, label_BTR70, label_T72,label_S2S1,label_BRDM_2,label_D7,label_SLICY,label_T62,label_ZIL131,label_ZSU_23_4))

    temp = np.array([image_list, label_list])
    temp = temp.transpose()
    np.random.shuffle(temp)
    
    image_list = list(temp[:, 0]) 
    label_list = list(temp[:, 1])  
   
    label_list = [int(float(i)) for i in label_list]
    print(image_list)

    print(label_list)
    
    return image_list, label_list


#%%
#生成相同大小的批次
def get_batch(image, label, image_W, image_H, batch_size, capacity):
    '''
    Args:
        image: list type
        label: list type
        image_W: image width
        image_H: image height
        batch_size: batch size
        capacity: the maximum elements in queue
    Returns:
        image_batch: 4D tensor [batch_size, width, height, 1 ], dtype=tf.float32
        label_batch: 1D tensor [batch_size], dtype=tf.int32
    '''
    
    image = tf.cast(image, tf.string)
    label = tf.cast(label, tf.int32)

    # make an input queue
    input_queue = tf.train.slice_input_producer([image, label])
    
    label = input_queue[1]
    image_contents = tf.read_file(input_queue[0])
    image = tf.image.decode_jpeg(image_contents, channels=1)
    
    ######################################
    # data argumentation 
    image = tf.random_crop(image, [96, 96, 1])# randomly crop the image size to 96 x 96
    image = tf.image.random_flip_left_right(image)
    #image = tf.image.random_brightness(image, max_delta=63)
    image = tf.image.random_contrast(image,lower=0.2,upper=1.8)

    ######################################
    
    #image = tf.image.resize_image_with_crop_or_pad(image, image_W, image_H)
    
    # if you want to test the generated batches of images, you might want to comment the following line.
    image = tf.image.per_image_standardization(image)
    
    image_batch, label_batch = tf.train.batch([image, label],
                                                batch_size= batch_size,
                                                num_threads= 64, 
                                                capacity = capacity)
    
    #you can also use shuffle_batch 
#    image_batch, label_batch = tf.train.shuffle_batch([image,label],
#                                                      batch_size=BATCH_SIZE,
#                                                      num_threads=64,
#                                                      capacity=CAPACITY,
#                                                      min_after_dequeue=CAPACITY-1)
    
    label_batch = tf.reshape(label_batch, [batch_size])
    image_batch = tf.cast(image_batch, tf.float32)
    
    return image_batch, label_batch


 
#%% TEST

# To test the generated batches of images
# When training the model, DO comment the following codes
"""
import matplotlib.pyplot as plt

BATCH_SIZE = 5
CAPACITY = 256
IMG_W = 128
IMG_H = 128

train_dir = '/Users/didizhang/Desktop/MSTAR/data/train/3_17_DEG/'

image_list, label_list = get_files(train_dir)
image_batch, label_batch = get_batch(image_list, label_list, IMG_W, IMG_H, BATCH_SIZE, CAPACITY)
 
with tf.Session() as sess:
    i = 0
    coord = tf.train.Coordinator()
    threads = tf.train.start_queue_runners(coord=coord)
    
    try:
        while not coord.should_stop() and i<1:
            
            img, label = sess.run([image_batch, label_batch])
            
            # just test one batch
            for j in np.arange(BATCH_SIZE):
                print('label: %d' %label[j])
                plt.imshow(img[j,:,:,0],cmap='gray')
                plt.show()
            i+=1
            
    except tf.errors.OutOfRangeError:
        print('done!')
    finally:
        coord.request_stop()
    coord.join(threads)
"""