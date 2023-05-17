from loguru import logger

class Score(object):
    def __int__(self):
        pass
    @staticmethod
    def _calculate_scores(predictions,labels):
        TP = 0
        FN = 0
        FP = 0
        TN = 0
        # 0 为 不一致(恶意), 1为一致(良性)
        for i, predict in enumerate(predictions):
            label = labels[i]
            if predict == 1 and predict == label:
                TP += 1
            elif predict == 1 and predict != label:
                FP += 1
            elif predict == 0 and predict == label:
                TN += 1
            elif predict == 0 and predict != label:
                FN += 1
            else:
                raise ValueError()
        accuracy = float(TP + TN) / (TP + FN + FP + TN) if (
            TP + FN + FP + TN) else 0
        precision = float(TP) / (TP + FP) if TP + FP else 0
        recall = float(TP) / (TP + FN) if TP + FN else 0
        score = (2 * precision * recall) / (precision+recall)
        return {"tp": TP, "fn": FN, "fp": FP, "tn": TN, "accuracy": accuracy,
                "precision": precision, "recall": recall, "score": score}

    @staticmethod
    def _logging_scores(scores):
        TP = scores["tp"]
        FN = scores["fn"]
        FP = scores["fp"]
        TN = scores["tn"]
        accuracy = scores["accuracy"]
        precision = scores["precision"]
        recall = scores["recall"]
        score = scores["score"]
        logger.info("[Result] TP: {TP}, FN: {FN}, FP: {FP}, TN: {TN}".format(
            TP=TP, FN=FN, FP=FP, TN=TN))
        logger.info("[Accuracy]: {accuracy}".format(accuracy=accuracy))
        logger.info("[Precision]: {precision}".format(precision=precision))
        logger.info("[Recall]: {recall}".format(recall=recall))
        logger.info("[Score]: {score}".format(score=score))