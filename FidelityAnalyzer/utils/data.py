import random

def split_set(samples, labels, test_percentage, shuffle=True, seed=None):
    if type(test_percentage) is not float:
        raise TypeError("Type of test_percentage must be float.")
    if not (0.0 <= test_percentage <= 1.0):
        raise ValueError("Argument test_percentage must be in range 0.0 to 1.0")

    complete_data = list(zip(samples, labels))
    groups = complete_data
    if seed:
        random.seed(seed)
    if shuffle:
        random.shuffle(complete_data)
    slice_point = int(len(complete_data) * (1 - test_percentage))
    train_data = groups[:slice_point]
    test_data = groups[slice_point:]
    # training_samples, training_labels = zip(*train_data)
    # test_samples, test_labels = zip(*test_data)
    return train_data, test_data