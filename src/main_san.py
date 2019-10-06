import os
import random

import numpy as np
from scipy.spatial.distance import cdist
import cv2

import torch
import torch.distributed as dist
import torch.nn as nn
import torch.nn.functional as F
# import torch.multiprocessing as mp
from torch.utils.data import DataLoader
from torch.optim import Adam
# from torch.utils.tensorboard import SummaryWriter
from scipy.spatial.distance import cdist
from package.model.san import SaN
from package.loss.san_loss import _SaN_loss
from package.dataset.data_san import *
from package.args.san_args import parse_config
from package.dataset.utils import make_logger
from package.model.utils import *


def update_lr(optimizer, lr):
    for param_group in optimizer.param_groups:
        param_group['lr'] = lr


def save_fn(save_dir, it, pre=0, mAP=0):
    return join(mkdir(join(save_dir, 'models')), 'Iter__{}__{}_{}.pkl'.format(it, int(pre * 1000), int(mAP * 1000)))


def _try_load(args, logger, model, optimizer):
    if args.start_from is None:
        # try to find the latest checkpoint
        files = os.listdir(mkdir(join(mkdir(args.save_dir), 'models')))
        if len(files) == 0:
            logger.info("Cannot find any checkpoint. Start new training.")
            return 0
        latest = max(files, key=lambda name: int(name.split('\\')[-1].split('/')[-1].split('.')[0].split('__')[1]))
        checkpoint = join(args.save_dir, 'models', latest)
    else:
        try: checkpoint = save_fn(args.save_dir, str(int(args.start_from)))
        except: checkpoint = args.start_from
    logger.info("Load model from {}".format(checkpoint))
    ckpt = torch.load(checkpoint, map_location='cpu')
    model.load_state_dict(ckpt['model'])
    optimizer.load_state_dict(ckpt['optimizer'])
    return ckpt['steps']


def _extract_feats(data_test, model, what, skip=1, batch_size=16):
    """
    :param data_test: test Dataset
    :param model: network model
    :param what: SK or IM
    :param skip: skip a certain number of image/sketches to reduce computation
    :return: a two-element list [extracted_labels, extracted_features]
    """
    labels = []
    feats = []
    for batch_idx, (xs, id) in \
            enumerate(data_test.traverse(what, skip=skip, batch_size=batch_size)):
        labels.append(model(xs.cuda()).data.cpu().numpy())
        # print(type(labels[0]), labels[0].shape)#     <class 'numpy.ndarray'> (16, 256)
        # print(type(id), id) # <class 'torch.Tensor'> tensor([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        feats.append(id.numpy())
    return np.concatenate(labels), np.concatenate(feats)


def _get_pre_from_matches(matches):
    return np.mean(matches)


def _get_map_from_matches(matches):
    s = 0
    for match in matches:
        count = 0
        for rank, ismatch in enumerate(match):
            s += ismatch * (count + 1) / (rank + 1)
            count += ismatch
    return s / matches.size


def _eval(feats_labels_sk, feats_labels_im, n):
    """
    Refer to https://blog.csdn.net/JNingWei/article/details/78955536 for mAP calculation
    :param feats_labels_sk: a two-element tuple [features_of_sketches, labels_of_sketches]
    :param feats_labels_im: a two-element tuple [features_of_images, labels_of_images]
    :param n: the top n elements used for evaluation
    :return: precision@n, mAP@n
    """
    # print(feats_labels_sk[0].shape, feats_labels_sk[1].shape, feats_labels_im[0].shape, feats_labels_im[1].shape)  # (16, 256) (16,) (16, 256) (16,)
    dists = cdist(feats_labels_sk[0], feats_labels_im[0], 'euclidean')
    # print("dists.shape=", dists.shape)  # (16, 16)
    ranks = np.argsort(dists, 0)
    # print("ranks.shape=", ranks.shape)  # (16, 16)
    ranksn = ranks[:n, :].T
    # print("ranksn.shape=", ranksn.shape)  # (16, 3)
    classesn = np.array([[feats_labels_im[1][i] == feats_labels_sk[1][r] for i in ranksn[r]] for r in range(len(ranksn))])
    # ("classesn.shape=", classesn.shape)  # (16, 3)
    # exit(0)
    return _get_pre_from_matches(classesn), _get_map_from_matches(classesn)


def train(args):
    # srun --gres=gpu --exclusive python main_san.py --steps 50000 --print_every 500 --save_every 200000 --batch_size 64 --dataset sketchy --margin 1
    if args.dataset == 'sketchy':
        sketch_folder = SKETCH_FOLDER_SKETCHY
        image_folder = IMAGE_FOLDER_SKETCHY
        train_class = TRAIN_CLASS_SKETCHY
        test_class = TEST_CLASS_SKETCHY
    elif args.dataset == 'tuberlin':
        sketch_folder = SKETCH_FOLDER_TUBERLIN
        image_folder = IMAGE_FOLDER_TUBERLIN
        train_class = TRAIN_CLASS_TUBERLIN
        test_class = TEST_CLASS_TUBERLIN
    else: raise Exception("dataset args error!")
    if args.sketch_dir != '': image_folder = args.sketch_dir
    if args.image_dir != '': sketch_folder = args.image_dir

    data_train = SaN_dataloader(folder_sk=sketch_folder, clss=train_class,
                                folder_im=image_folder, normalize01=False, doaug=False)
    dataloader_train = DataLoader(dataset=data_train, batch_size=args.batch_size, shuffle=False)

    data_test = SaN_dataloader(folder_sk=sketch_folder, exp3ch=True, clss=test_class,
                               folder_im=image_folder, normalize01=False, doaug=False)

    model = SaN()
    model.cuda()
    optimizer = Adam(params=model.parameters(), lr=args.lr, weight_decay=args.l2_reg)
    logger = make_logger(join(mkdir(args.save_dir), curr_time_str() + '.log'))
    steps = _try_load(args, logger, model, optimizer)
    logger.info(str(args))
    args.steps += steps
    san_loss = _SaN_loss(args.margin)
    while True:
        loss_sum = []
        model.train()
        for _, (sketch, positive_image, negative_image, positive_class_id) in enumerate(dataloader_train):
            optimizer.zero_grad()
            loss = san_loss(model(sketch.cuda()),
                            model(positive_image.cuda()),
                            model(negative_image.cuda()))
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            loss_sum.append(float(loss.item()))
            if (steps + 1) % args.save_every == 0:
                model.eval()
                n = 50; skip = 1
                feats_labels_sk = _extract_feats(data_test, model, SK, skip=skip, batch_size=args.batch_size)
                feats_labels_im = _extract_feats(data_test, model, IM, skip=skip, batch_size=args.batch_size)
                pre, mAP = _eval(feats_labels_sk, feats_labels_im, n)
                logger.info("Precision@{}: {}, mAP@{}: {}".format(n, pre, n, mAP) +
                            "  " + 'step: {},  loss: {}'.format(steps, np.mean(loss_sum)))
                torch.save({'model': model.state_dict(),
                            'optimizer': optimizer.state_dict(),
                            'steps': steps,
                            'args': args},
                           save_fn(args.save_dir, steps, pre, mAP))

            if (steps + 1) % args.print_every == 0:
                print('step: {},  loss: {}'.format(steps, np.mean(loss_sum)))
                loss_sum = []

            steps += 1
            if steps >= args.steps: break
        if steps >= args.steps: break


if __name__ == '__main__':
    args = parse_config()
    train(args)