import torch
import torch.nn as nn
import torch.nn.functional as F

from pytorch_modules.nn.utils import ConvNormAct, SeparableConvNormAct


class FPN(nn.Module):
    def __init__(self, channels_list, out_channels=[512, 256, 128], reps=3):
        """[summary]
        
        Arguments:
            channels_list {list} -- channels of feature maps, from high levels to low levels
        
        Keyword Arguments:
            out_channels {list} -- out channels  (default: {[512, 256, 128]})
            reps {int} -- repeat times (default: {3})
        """
        super(FPN, self).__init__()
        self.fpn_list = nn.ModuleList([])
        self.trans = nn.ModuleList([])
        self.intrans = nn.ModuleList([])
        self.relu = nn.ReLU(True)
        last_channels = 0
        for i in range(len(channels_list)):
            if i > 0:
                self.trans.append(
                    ConvNormAct(last_channels,
                                out_channels[i],
                                1,
                                activate=nn.ReLU(True)))
                last_channels = out_channels[i]
            self.intrans.append(
                ConvNormAct(channels_list[i],
                            out_channels[i],
                            1,
                            activate=nn.ReLU(True)))
            in_channels = out_channels[i] + last_channels
            fpn = [
                ConvNormAct(in_channels,
                            out_channels[i],
                            1,
                            activate=nn.ReLU(True))
            ]
            fpn += [
                SeparableConvNormAct(out_channels[i],
                                     out_channels[i],
                                     mid_activate=nn.ReLU(True),
                                     activate=nn.ReLU(True))
                for rep in range(reps)
            ]
            fpn = nn.Sequential(*fpn)
            self.fpn_list.append(fpn)
            last_channels = out_channels[i]
        # self.float_functional = nn.quantized.FloatFunctional()

    def forward(self, features):
        features = [self.intrans[i](f) for i, f in enumerate(features)]
        new_features = []
        for i in range(len(self.fpn_list)):
            feature = features[i]
            if len(new_features):
                last_feature = self.trans[i - 1](new_features[-1])
                last_feature = F.interpolate(last_feature,
                                             scale_factor=2,
                                             mode='bilinear',
                                             align_corners=False)
                if hasattr(self, 'float_functional'):
                    feature = self.float_functional.cat(
                        [last_feature, feature], 1)
                else:
                    feature = torch.cat([last_feature, feature], 1)
            feature = self.fpn_list[i](feature)
            new_features.append(feature)
        return new_features
