import torch
import torch.nn as nn
from sentence_transformers import SentenceTransformer


class Embedder(nn.Module):
    def __init__(self, bert, bert_size=768, num_classes=26, class_emb_size=6):
        super().__init__()
        self.text_embedder = bert
        self.UI_embedder = nn.Embedding(num_classes, class_emb_size).cuda()
        self.bert_size = bert_size
        self.class_size = class_emb_size

    def forward(self, widget_text, widget_class, widget_clickable):
        if len(widget_clickable) == 1:
            n_batch = 1
        else:
            n_batch = len(widget_clickable)
        widget_embedding_list = []
        for batch_i in range(n_batch):
            text_emb = torch.tensor(self.text_embedder.encode(widget_text[batch_i]),device=0)
            class_emb = self.UI_embedder(torch.tensor(widget_class[batch_i], device=0))
            x = torch.cat((text_emb,class_emb),-1)
            for index in range(len(widget_text[batch_i])):
                if widget_text[batch_i][index] == '':
                    x[index] = torch.zeros(self.bert_size + self.class_size).cuda()
            x = torch.cat((x, torch.tensor(widget_clickable[batch_i],device=0).unsqueeze(-1)), -1)
            widget_embedding_list.append(x)
        return widget_embedding_list

class WidgetEmbed(nn.Module):
    def __init__(self, bert, bert_size=768, num_classes=26, class_emb_size=6, clickable_size = 1):
        super().__init__()
        self.embedder = Embedder(bert, bert_size, num_classes).cuda()
        self.lin = nn.Linear(bert_size + class_emb_size+clickable_size, bert_size)
        self.lin.cuda()

    def forward(self, widget_inputs):
        widget_text = widget_inputs[0]
        widget_class = widget_inputs[1]
        widget_clickable = widget_inputs[2]
        input_vector = self.embedder(widget_text, widget_class,widget_clickable)
        output_list = []
        for item_widget in input_vector:
            output = self.lin(item_widget)
            output_list.append(output)
        return output_list