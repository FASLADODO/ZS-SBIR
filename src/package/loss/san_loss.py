import torch
import torch.nn as nn

# _SaN_loss = nn.CrossEntropyLoss()

class _SaN_loss(nn.Module):
    """
    SaN loss is actually a triplet loss
    """
    def __init__(self, margin):
        super(_SaN_loss, self).__init__()
        self.D = lambda x, y: torch.sum((x - y) ** 2, 1)
        self.margin = margin

    def forward(self, sketch_feat, positive_image_feat, negative_image_feat):
        features_diff = self.margin + self.D(sketch_feat, positive_image_feat) - self.D(sketch_feat, negative_image_feat)
        # print("features_diff shape=", features_diff.shape)
        # features_diff[features_diff < 0] = 0
        features_diff = torch.max(input=features_diff, other=torch.zeros(features_diff.size(0)).cuda())
        # print("this done features_diff.shape=", features_diff.shape) # this done features_diff.shape= torch.Size([16])
        return torch.mean(features_diff)
