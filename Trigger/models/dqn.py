import torch
import torch.nn as nn
import torch.nn.functional as F
from sentence_transformers import SentenceTransformer,util
from models.widget_embed import WidgetEmbed
from models.replay_memory import ReplayMemory,Transition
from models.autoencoder import LayoutAutoEncoder
import numpy as np
from xml.etree import ElementTree as ET
import uuid
from utils.widget_util import parse_widgets,generate_udid_str
import random
from loguru import logger
from utils.screen_util import image_match
import pytesseract
from io import BytesIO
from PIL import Image
import imgsim

class MultiModal2Vec(nn.Module):
    def __init__(self,bert_size=768, addition_visual_size = 768, addition_layout_size=64, addition_coords = 4):
        super(MultiModal2Vec,self).__init__()
        self.bert_size = bert_size
        self.net = nn.RNN(bert_size + addition_coords + 1, bert_size) # 1 visit count
        self.lin = nn.Linear(self.bert_size + addition_visual_size + addition_layout_size, self.bert_size)
        self.lin.weight.data.normal_(0, 0.1)

    def forward(self,widget_embeddings, visual_feature, layout_feature,trace_screen_lengths):
        batch_size = len(widget_embeddings)
        screen_embeddings = torch.empty(batch_size, 1, self.bert_size,device=0)
        for batch_num in range(batch_size):
            widget_set = widget_embeddings[batch_num]
            if trace_screen_lengths is not None:
                input = torch.nn.utils.rnn.pack_padded_sequence(widget_set, trace_screen_lengths[batch_num],enforce_sorted=False)
            else:
                input = widget_set
            full_output, h = self.net(input)
            h = h[0]
            if visual_feature is not None:
                concat_emb = torch.cat((h, visual_feature[batch_num].view(1,-1)), dim=1)
            else:
                concat_emb = h
            if layout_feature is not None:
                concat_emb = torch.cat((concat_emb, layout_feature[batch_num].view(1,-1).cuda()), dim=1)
            final_emb = self.lin(concat_emb)
            screen_embeddings[batch_num] = final_emb
        return screen_embeddings

class Net(nn.Module):
    def __init__(self,bert,bert_size = 768):
        super(Net, self).__init__()
        self.bert = bert
        self.widget_model = WidgetEmbed(self.bert)
        self.multimodalModel = MultiModal2Vec()
        self.dense_layer1 = nn.Linear(bert_size,100).cuda()
        self.dense_layer2 = nn.Linear(100, 100).cuda()
        self.out = nn.Linear(100,100).cuda()

    def parse_single_label_texts(self,labeled_text_tmp):
        widget_clickable = [widget[3] for widget in labeled_text_tmp]
        widget_text = [widget[0] for widget in labeled_text_tmp]
        widget_class = [widget[1] for widget in labeled_text_tmp]
        widget_coords = [widget[2] for widget in labeled_text_tmp]
        return widget_clickable,widget_text,widget_class,widget_coords

    def forward(self,observation):
        visual_feature, layout_feature, labeled_text_tmp, visit_count,shallow_visit_count = observation
        n_widget_click_list = []
        n_widget_text = []
        n_widget_class_list = []
        n_widget_coords = []
        for text_item in labeled_text_tmp:
            widget_click_s,widget_text_s,widget_class_s,widget_coords_s = self.parse_single_label_texts(text_item)
            n_widget_click_list.append(widget_click_s)
            n_widget_text.append(widget_text_s)
            n_widget_class_list.append(widget_class_s)
            n_widget_coords.append(widget_coords_s)
        widget_clickable = n_widget_click_list
        widget_class = n_widget_class_list
        widget_text = n_widget_text
        widget_coords = n_widget_coords
        widget_embeddings = self.widget_model([widget_text, widget_class, widget_clickable])
        coords_flag = True
        if coords_flag:
            for batch_i in range(len(widget_embeddings)):
                widget_coords_tensor = torch.tensor(widget_coords[batch_i],device=0)
                widget_embeddings[batch_i] = torch.cat((widget_embeddings[batch_i], widget_coords_tensor), dim=-1)
        visit_flag = True
        if visit_flag:
            for batch_i in range(len(widget_embeddings)):
                visit_count_tensor = torch.tensor(visit_count[batch_i],device=0)
                widget_embeddings[batch_i] = torch.cat((widget_embeddings[batch_i], visit_count_tensor.unsqueeze(-1)), dim=-1).unsqueeze(-2)
        widget_embedding_adjust = widget_embeddings
        visual_feature_adjust = visual_feature
        layout_feature_adjust = layout_feature
        combined_feature = self.multimodalModel(widget_embedding_adjust,visual_feature_adjust,layout_feature_adjust,None)
        combined_feature = F.relu(combined_feature.squeeze(1))
        hidden_layer1 = F.relu(self.dense_layer1(combined_feature))
        hidden_layer2 = F.relu(self.dense_layer2(hidden_layer1))
        action_prob = self.out(hidden_layer2)
        return action_prob


class DQN(nn.Module):
    def __init__(self):
        super(DQN, self).__init__()
        self.bert = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')#distiluse-base-multilingual-cased-v1
        self.eval_net, self.target_net = Net(self.bert).cuda(), Net(self.bert).cuda()

        self.layout_autoencoder = LayoutAutoEncoder()
        self.layout_autoencoder.load_state_dict(torch.load('pretrainedModel/layout_encoder.ep800'))
        self.vtr = imgsim.Vectorizer(device='cuda')

        self.learn_step_counter = 0
        self.memory = ReplayMemory(1000000)
        self.tmp_memory = ReplayMemory(10000)
        self.optimizer = torch.optim.Adam(self.eval_net.parameters(), lr=0.01)
        self.loss_func = nn.MSELoss()
        self.EPISILO = 0.7
        self.GAMMA = 0.90
        self.NUM_ACTIONS = 100
        self.Q_NETWORK_ITERATION = 100
        self.BATCH_SIZE = 32
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    def check_visit_finish(self,app,widgets):
        for item in widgets:
            widget = app.currentGUI.widget_dict[item]
            if widget.visitCount <= widget.maxVisitCount:
                logger.info('widget.visitCount,',str(widget.visitCount))
                return False
        return True

    def get_visit_count_mask_child(self,app,visit_count):
        vc_mask = []
        for visit in visit_count:
            vc_mask.append(1.0 / (visit * 10 + 1))
        if len(vc_mask) == 0:
            return None
        else:
            app.current_mask[0:len(vc_mask)] = [1] * len(vc_mask)
        return vc_mask

    def choose_action(self, app):
        state = app.observation
        widget_shallow_visit_count = state[4][0]
        if len(widget_shallow_visit_count) < 1:
            return None, None, None
        vc_mask = self.get_visit_count_mask_child(app,widget_shallow_visit_count)
        if np.random.randn() <= self.EPISILO:
            action_value = self.eval_net.forward(state)
            nn_softmax = torch.nn.Softmax(dim=1)
            action_value = nn_softmax(action_value)
            len_vc_mask = len(vc_mask)
            # print('vc mask ',vc_mask)
            if vc_mask is not None:
                vc_mask.extend([0]*(len(app.current_mask)-len(vc_mask)))
                action_value = action_value.cpu() * torch.tensor(vc_mask)
            action_value = action_value.cpu() * torch.tensor(app.current_mask).unsqueeze(0)
            # print(action_value[0][0:len_vc_mask])
            action = torch.max(action_value, 1)[1].data.numpy()
            action = action[0]
            print('model: current action, ', action)
        else:
            random_len = np.count_nonzero(app.current_mask)
            action = np.random.randint(0,random_len)
            action = action
            print('random: current action, ', action)
        print('current usable widgets ',len(app.usable_widgets))
        if action < len(app.usable_widgets):
            widget_uuid= app.usable_widgets[action]
            operatable_widget = app.all_widget_dict[widget_uuid]
            return state, action, operatable_widget
        print('no state, no action, no widget')
        return None, None, None

    def store_transition(self, state, action, next_state, reward):
        self.memory.push(state, action, next_state, reward)
        self.tmp_memory.push(state, action, next_state, reward)

    def parse_batch_state2(self,batch_states):
        visual_feature, layout_feature, labeled_text_tmp = [],[],[]
        for s in batch_states:
            visual_feature.append(s[0])
            layout_feature.append(s[1])
            labeled_text_tmp.extend(s[2])
        visual_features = torch.cat(visual_feature).to(self.device)
        layout_features = torch.cat(layout_feature).to(self.device)
        return [visual_features,layout_features,labeled_text_tmp]

    def parse_batch_state(self,batch_states):
        visual_feature, layout_feature, labeled_text_tmp, visit_count, shallow_visit_count = [],[],[],[],[]
        for s in batch_states:
            visual_feature.append(s[0])
            layout_feature.append(s[1])
            labeled_text_tmp.extend(s[2])
            visit_count.extend(s[3])
            shallow_visit_count.extend(s[4])
        visual_features = torch.cat(visual_feature).to(self.device)
        layout_features = torch.cat(layout_feature).to(self.device)
        return [visual_features,layout_features,labeled_text_tmp,visit_count,shallow_visit_count]

    def learn(self,commands):
        if self.learn_step_counter % self.Q_NETWORK_ITERATION ==0:
            self.target_net.load_state_dict(self.eval_net.state_dict())
        self.learn_step_counter+=1
        print('Now training steps is ',self.learn_step_counter,' steps')
        if commands == 'currentApp':
            transitions = self.tmp_memory.sample(self.BATCH_SIZE)
        else:
            transitions = self.memory.sample(self.BATCH_SIZE)
        batch = Transition(*zip(*transitions))
        batch_next_state = self.parse_batch_state(batch.next_state)
        batch_state = self.parse_batch_state(batch.state)
        batch_action = torch.tensor(batch.action).unsqueeze(1).cuda()
        batch_reward = torch.tensor(batch.reward).unsqueeze(1).cuda()

        q_eval = self.eval_net(batch_state).gather(1, batch_action)
        q_next = self.target_net(batch_next_state).detach()
        q_target = batch_reward + self.GAMMA * q_next.max(1)[0].view(self.BATCH_SIZE, 1)
        self.loss = self.loss_func(q_eval, q_target)

        self.optimizer.zero_grad()
        self.loss.backward(retain_graph=True)
        self.optimizer.step()