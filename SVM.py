import sys

from sklearn.multiclass import OneVsRestClassifier
from sklearn.svm import SVC
import numpy as np
from sklearn.metrics import accuracy_score

# 给训练集分组
def fold_split(dataset_idx, n_fold):
    # 获取训练样本数量
    n_samples = len(dataset_idx)
    # 确定每一份训练集的大小
    fold_sizes = np.floor(n_samples / n_fold) * np.ones(n_fold, dtype=int)
    # 分配剩下的样本
    r = n_samples % n_fold
    for i in range(r):
        fold_sizes[i] += 1

    train_indices = []
    # 这里采用的是交叉验证的方式划分训练集，比如要划分11份训练集，那就将样本划分11份，然后每个样本依次选10份
    current = 0
    for fold_size in fold_sizes:
        start, stop = current, current + int(fold_size)
        test_mask = np.zeros(n_samples, dtype=np.bool_)
        test_mask[start:stop] = True
        train_mask = np.logical_not(test_mask)
        train_indices.append(dataset_idx[train_mask])
        current = stop

    return train_indices

# 处理训练集的标签，分为C类和no类
def training_data_process(dataset, train_idx, C):
    training_data = dataset.iloc[train_idx]
    # 得到训练集标签名称
    label_class = training_data.columns[-1]
    for i in train_idx:
        if training_data.loc[i, label_class] != C:
            training_data.loc[i, label_class] = 0
        else:
            training_data.loc[i, label_class] = 1
    return training_data

# 预测，最后加权集成分类结果
def weigth(SVM, train_data, classification_list):
    predicted = []
    for i in range(train_data.shape[0]):
        features_test = train_data.iloc[i:i+1, :-1]
        predict_dict = {}
        for C in classification_list:
            de_f = SVM[C].decision_function(features_test)
            predict_dict[C] = de_f[0]
        result = max(predict_dict, key=predict_dict.get)
        predicted.append(result)
    labels_test = train_data[train_data.columns[-1]]

    # print("predict:\n", predicted)
    # print("labels_test:\n", labels_test)
    acc = accuracy_score(predicted, labels_test)

    return acc

def SVM(dataset, dataset_idx):
    classification_list = np.unique(dataset[dataset.columns[-1]])
    train_set_num = len(classification_list)
    train_idx = fold_split(dataset_idx, n_fold=train_set_num)

    # 训练模糊随机森林生成决策树
    svm = {}
    for i in range(len(classification_list)):
        # 选取训练集
        print(f"正在生成类别{classification_list[i]}的SVM训练集")
        training_data = training_data_process(dataset, train_idx[i], classification_list[i])
        features_train = training_data[training_data.columns[:-1]]
        labels_train = training_data[training_data.columns[-1]]
        # n_estimators表示迭代的次数
        print(f"正在生成类别{classification_list[i]}的SVM模型")
        SVM = OneVsRestClassifier(SVC(kernel='rbf')).fit(features_train, labels_train.astype(int))
        svm[classification_list[i]] = SVM
        print("="*40)
    print("正在计算SVM支持向量机的权重！")
    weigthSVM = weigth(svm, dataset.iloc[dataset_idx], classification_list)
    print(f"已完成各类别一对多SVM分类器的生成！")
    print("="*40)
    return svm, weigthSVM
