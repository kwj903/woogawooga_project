import torch
import numpy as np

class EnsemblePhishingDetector:
    def __init__(self, models, weights=None):
        self.models = models
        self.weights = weights if weights else [1.0 / len(models)] * len(models)
    
    def predict(self, input_ids, attention_mask, lengths):
        all_probs = []
        
        for model in self.models:
            model.eval()
            with torch.no_grad():
                outputs = model(input_ids=input_ids, attention_mask=attention_mask, lengths=lengths)
                probs = torch.softmax(outputs, dim=1)
                all_probs.append(probs.cpu().numpy())
        
        # 가중 평균 계산
        weighted_probs = np.zeros_like(all_probs[0])
        for i, prob in enumerate(all_probs):
            weighted_probs += self.weights[i] * prob
        
        return weighted_probs