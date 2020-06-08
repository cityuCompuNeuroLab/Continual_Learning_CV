import torch

import utils


####-----------------------------####
####----model evaluation----####
####-----------------------------####


def validate(model, dataset, batch_size=32, test_size=1024, verbose=True, allowed_classes=None,
             with_exemplars=False, task=None):
    '''Evaluate precision (= accuracy or proportion correct) of a classifier ([model]) on [dataset].
    [allowed_classes]   None or <list> containing all "active classes" between which should be chosen
                            (these "active classes" are assumed to be contiguous)'''

    # Set model to eval()-mode
    mode = model.training
    model.eval()

    # Loop over batches in [dataset]
    data_loader = utils.get_data_loader(dataset, batch_size, cuda=model._is_on_cuda())
    total_tested = total_correct = 0
    for data, labels in data_loader:
        # -break on [test_size] (if "None", full dataset is used)
        if test_size:
            if total_tested >= test_size:
                break
        # -evaluate model (if requested, only on [allowed_classes])
        data, labels = data.to(model._device()), labels.to(model._device())
        # labels = labels - allowed_classes[0] if (allowed_classes is not None) else labels
        with torch.no_grad():
            if with_exemplars:
                predicted = model.classify_with_exemplars(data, allowed_classes=allowed_classes)
                # - in case of Domain-IL scenario, collapse all corresponding domains into same class
                if max(predicted).item() >= model.classes:
                    predicted = predicted % model.classes
            else:
                scores = model(data) if (allowed_classes is None) else model(data)[:, allowed_classes]
                _, predicted = torch.max(scores, 1)
        # -update statistics
        total_correct += (predicted == labels).sum().item()
        total_tested += len(data)
    precision = total_correct / total_tested

    # Set model back to its initial mode, print result on screen (if requested) and return it
    model.train(mode=mode)
    if verbose:
        print('=> precision: {:.3f}'.format(precision))
    return precision


def validate5(model, dataset, batch_size=32, test_size=1024, verbose=True, allowed_classes=None,
              with_exemplars=False, task=None):
    '''Evaluate precision (= accuracy or proportion correct) of a classifier ([model]) on [dataset].
    [allowed_classes]   None or <list> containing all "active classes" between which should be chosen
                            (these "active classes" are assumed to be contiguous)'''

    # Set model to eval()-mode
    mode = model.training
    model.eval()

    # Loop over batches in [dataset]
    data_loader = utils.get_data_loader(dataset, batch_size, cuda=model._is_on_cuda())
    total_tested = total_correct = 0
    for data, labels in data_loader:
        # -break on [test_size] (if "None", full dataset is used)
        if test_size:
            if total_tested >= test_size:
                break
        # -evaluate model (if requested, only on [allowed_classes])
        data, labels = data.to(model._device()), labels.to(model._device())
        # labels = labels - allowed_classes[0] if (allowed_classes is not None) else labels
        with torch.no_grad():
            if with_exemplars:
                predicted = model.classify_with_exemplars(data, allowed_classes=allowed_classes)
                # - in case of Domain-IL scenario, collapse all corresponding domains into same class
                if max(predicted).item() >= model.classes:
                    predicted = predicted % model.classes
            else:
                scores = model(data) if (allowed_classes is None) else model(data)[:, allowed_classes]
                _, predicted = scores.topk(1, -1)
        # -update statistics
        for i in range(5):
            total_correct += (predicted[:, i] == labels).sum().item()
        total_tested += len(data)
    precision = total_correct / total_tested

    # Set model back to its initial mode, print result on screen (if requested) and return it
    model.train(mode=mode)
    if verbose:
        print('=> precision: {:.3f}'.format(precision))
    return precision


def initiate_precision_dict(n_tasks):
    '''Initiate <dict> with all precision-measures to keep track of.'''
    precision = {}
    precision["all_tasks"] = [[] for _ in range(n_tasks)]
    precision["average"] = []
    precision["x_iteration"] = []
    precision["x_task"] = []
    return precision


def precision(model, datasets, current_task, iteration, classes_per_task=None,
              precision_dict=None, test_size=None, verbose=False, summary_graph=True,
              with_exemplars=False):
    '''Evaluate precision of a classifier (=[model]) on all tasks so far (= up to [current_task]) using [datasets].
    [precision_dict]    None or <dict> of all measures to keep track of, to which results will be appended to
    [classes_per_task]  <int> number of active classes er task'''

    # Evaluate accuracy of model predictions for all tasks so far (reporting "0" for future tasks)
    n_tasks = len(datasets)
    precs = []
    for i in range(n_tasks):
        if i + 1 <= current_task:
            allowed_classes = None
            precs.append(validate(model, datasets[i], test_size=test_size, verbose=verbose,
                                  allowed_classes=allowed_classes, with_exemplars=with_exemplars,
                                  task=i + 1))
        else:
            precs.append(0)
    average_precs = sum([precs[task_id] for task_id in range(current_task)]) / current_task

    # Print results on screen
    if verbose:
        print(' => ave precision: {:.3f}'.format(average_precs))

    names = ['task {}'.format(i + 1) for i in range(n_tasks)]

    # Append results to [progress]-dictionary and return
    if precision_dict is not None:
        for task_id, _ in enumerate(names):
            precision_dict["all_tasks"][task_id].append(precs[task_id])
        precision_dict["average"].append(average_precs)
        precision_dict["x_iteration"].append(iteration)
        precision_dict["x_task"].append(current_task)
    return precision_dict
