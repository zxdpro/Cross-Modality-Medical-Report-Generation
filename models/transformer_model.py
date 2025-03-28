import numpy as np
import json
import torch
import torch.nn as nn

from modules.vanilla_transformer import BaseCMN
from modules.visual_extractor import VisualExtractor

class BaseCMNModel(nn.Module):
    def __init__(self, args, tokenizer):
        super(BaseCMNModel, self).__init__()
        self.args = args
        self.tokenizer = tokenizer
        self.visual_extractor = VisualExtractor(args)
        self.encoder_decoder = BaseCMN(args, tokenizer)

        if args.dataset_name == 'iu_xray':
            self.forward = self.forward_iu_xray
        else:
            self.forward = self.forward_mimic_cxr

    def __str__(self):
        model_parameters = filter(lambda p: p.requires_grad, self.parameters())
        params = sum([np.prod(p.size()) for p in model_parameters])
        return super().__str__() + '\nTrainable parameters: {}'.format(params)
    
    def forward_iu_xray(self, images, targets=None, retrival_ids=None, mode='train', update_opts={}):
        att_feats_0, fc_feats_0 = self.visual_extractor(images[:, 0])
        att_feats_1, fc_feats_1 = self.visual_extractor(images[:, 1])
        fc_feats = torch.cat((fc_feats_0, fc_feats_1), dim=1)      #[bs, 4096]
        att_feats = torch.cat((att_feats_0, att_feats_1), dim=1)   #[bs, 98, 2048]
        if mode == 'train':
            output = self.encoder_decoder(fc_feats, att_feats, targets, retrival_ids=retrival_ids, mode='forward')
            return output
        elif mode == 'sample':
            # print(retrival_ids)
            output, output_probs = self.encoder_decoder(fc_feats, att_feats, retrival_ids=retrival_ids, mode='sample', update_opts=update_opts)
            return output, output_probs
        else:
            raise ValueError

    def forward_mimic_cxr(self, images, targets=None, mode='train', update_opts={}):
        if  self.args.use_rebuild_data:
            att_feats_0, fc_feats_0 = self.visual_extractor(images[:, 0])
            att_feats_1, fc_feats_1 = self.visual_extractor(images[:, 1])
            fc_feats = fc_feats_0 - fc_feats_1 + fc_feats_0
            att_feats = att_feats_0 - att_feats_1 + att_feats_0
            #fc_feats = torch.cat((fc_feats_0, fc_feats_1), dim=1)
            #att_feats = torch.cat((att_feats_0, att_feats_1), dim=1)
        else:
            att_feats, fc_feats = self.visual_extractor(images)
        if mode == 'train':
            output = self.encoder_decoder(fc_feats, att_feats, targets, mode='forward')
            return output
        elif mode == 'sample':
            output, output_probs = self.encoder_decoder(fc_feats, att_feats, mode='sample', update_opts=update_opts)
            return output, output_probs
        else:
            raise ValueError
