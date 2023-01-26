from DataLoaders.dataset import Dataset
# from TransferlerarningModels.transfer_learning import Resnet50 as load_model
from DataLoaders.XLS_utils import XLS
from Pytorch_model.unet import UNet as load_model
# from ConnectedSegnet.connectedSegnet_model import ConSegnetsModel as load_model
import DataLoaders.config as config
import math
import sys
import os
from torch.nn import CrossEntropyLoss as Loss
from torch.optim import Adam,RMSprop,NAdam
from torch.utils.data import DataLoader,SubsetRandomSampler
from torchvision import transforms
import matplotlib.pyplot as plt
import torch
import random
import time
from qqdm import qqdm, format_str
from DataLoaders.scores import scores
import numpy 
from sklearn.model_selection import KFold
from engine import testing,training
import json


def collate_fn(batch):
    return tuple(zip(*batch))

def get_model():
    if config.LOAD_NEW_MODEL:
        # kwargs = dict({"num_classes":config.NUM_CLASSES})
        model = load_model(4)
        
        # model.conv1.in_channels = config.NUM_CHANNELS
        # model.fc.out_features = config.NUM_CLASSES

        print("Random Weighted ModelS loaded.")
        # print(model)

        return model.to(config.DEVICE)
    else:
        model = load_model(4)
        print("############# Previous weights loaded. ###################")
        model.load_state_dict(torch.load(config.MODEL_PATH))
        
        # print(model.classifier)
        # model.classifier = torch.nn.Linear(1024,config.NUM_CLASSES)

        # for name,param in model.named_parameters():
        #     print(name,param.requires_grad)

        return model.to(config.DEVICE)

def get_dataset():
    train,test = XLS().return_datasets()

    train = Dataset(train,True)
    test = Dataset(test,False)

    return train, test

def get_others(model):

    lossFunc = Loss()
    # opt = RMSprop(model.parameters(),lr=config.INIT_LR)
    opt = Adam(model.parameters(), lr=config.INIT_LR,weight_decay=1e-6)
    print("LossFunc:",lossFunc)
    print("Optimizer:",opt)

    return lossFunc,opt


def save_model_and_metrics(model,fold_metrics):
    print("/nSaving Model...")
    name = "model_"+model.__class__.__name__+".pth"
    print(name)
    if name not in os.listdir(config.BASE_OUTPUT):
        torch.save(model.state_dict(), os.path.join(config.BASE_OUTPUT,name))
    
    jso = json.dumps(fold_metrics)
    f = open(f"output/metrics_{model.__class__.__name__}.json","a")
    f.write(jso)
    f.close()
    

def get_dataloaders(train_valDS,train_sampler,val_sampler):
    trainLoader = DataLoader(train_valDS,sampler=train_sampler, shuffle=False, batch_size=config.BATCH_SIZE, num_workers=0,collate_fn=collate_fn)
    valLoader = DataLoader(train_valDS,sampler=val_sampler, shuffle=False, batch_size=config.BATCH_SIZE, num_workers=0,collate_fn=collate_fn)

    return trainLoader, valLoader
    
def base():
    train_valDS, testDS = get_dataset()
    model = get_model()
    lossFunc, opt= get_others(model)

    print(f"[INFO] found {len(train_valDS)} examples in the training set...")
    print(f"[INFO] found {len(testDS)} examples in the test set...")
    
    total_time_start = time.time()

    metrics = {"training":[],"test":[]}

    testLoader = DataLoader(testDS,config.BATCH_SIZE,shuffle=False,sampler=testDS.sampler,num_workers=0,collate_fn=collate_fn)


    if config.K_FOLD:
        kfold = KFold(n_splits=config.CV_K_FOLDS, shuffle=True)
        for fold, (train_ids, valid_ids) in enumerate(kfold.split(train_valDS)):
            print(f'FOLD {fold}')
            print('--------------------------------')
            train_sampler = SubsetRandomSampler(train_ids)
            val_sampler = SubsetRandomSampler(valid_ids)
            trainLoader, valLoader = get_dataloaders(train_valDS,train_sampler, val_sampler)

            training_metrics = training(model,trainLoader,lossFunc,opt,valLoader,fold)
            metrics["training"].append(training_metrics)

            test_metrics = testing(model,lossFunc,testLoader)
            metrics["test"].append(test_metrics)
    
    else:
        trainLoader = DataLoader(train_valDS,config.BATCH_SIZE,sampler=train_valDS.sampler,num_workers=0,collate_fn=collate_fn)
        training_metrics = training(model,trainLoader,lossFunc,opt)
        metrics["training"].append(training_metrics)

        test_metrics = testing(model,lossFunc,testLoader)
        metrics["test"].append(test_metrics)

    total_time = int(time.time()-total_time_start)/60
    print(f"---------- Training_time:{total_time} minute ----------")
    save_model_and_metrics(model,metrics)
    
if __name__ == "__main__":
    base()