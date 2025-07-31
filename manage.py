#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

# pickle 로드를 위한 EnsemblePhishingDetector 클래스 정의
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    import numpy as np
    from transformers import AutoModel
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.svm import SVC
    from sklearn.feature_extraction.text import TfidfVectorizer
    from scipy.sparse import hstack
    
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
    
    # ImprovedmBERTClassifier 클래스 정의 (앙상블 모델 로드용)
    class ImprovedmBERTClassifier(nn.Module):
        def __init__(self, base_model=None, n_classes=2, dropout=0.3):
            super(ImprovedmBERTClassifier, self).__init__()
            if base_model is None:
                try:
                    self.base_model = AutoModel.from_pretrained('bert-base-multilingual-cased')
                except:
                    self.base_model = None
            else:
                self.base_model = base_model
            
            if self.base_model:
                self.dropout = nn.Dropout(dropout)
                hidden_size = self.base_model.config.hidden_size
                self.classifier = nn.Sequential(
                    nn.Linear(hidden_size, hidden_size // 2), 
                    nn.ReLU(), 
                    nn.Dropout(dropout),
                    nn.Linear(hidden_size // 2, hidden_size // 4), 
                    nn.ReLU(), 
                    nn.Dropout(dropout),
                    nn.Linear(hidden_size // 4, n_classes)
                )
                self.layer_norm = nn.LayerNorm(hidden_size)
        
        def forward(self, input_ids, attention_mask):
            if self.base_model is None:
                return torch.zeros((input_ids.size(0), 2))
            
            outputs = self.base_model(input_ids=input_ids, attention_mask=attention_mask)
            cls_output = outputs.last_hidden_state[:, 0, :]
            normalized_output = self.layer_norm(cls_output)
            output = self.dropout(normalized_output)
            output = self.classifier(output)
            return output
    
    # ImprovedKoELECTRAClassifier 클래스 정의
    class ImprovedKoELECTRAClassifier(nn.Module):
        def __init__(self, base_model, n_classes=2, dropout=0.3):
            super(ImprovedKoELECTRAClassifier, self).__init__()
            self.base_model = base_model
            self.dropout = nn.Dropout(dropout)
            hidden_size = self.base_model.config.hidden_size
            self.classifier = nn.Sequential(
                nn.Linear(hidden_size, hidden_size // 2), 
                nn.ReLU(), 
                nn.Dropout(dropout),
                nn.Linear(hidden_size // 2, hidden_size // 4), 
                nn.ReLU(), 
                nn.Dropout(dropout),
                nn.Linear(hidden_size // 4, n_classes)
            )
            self.layer_norm = nn.LayerNorm(hidden_size)
        
        def forward(self, input_ids, attention_mask):
            outputs = self.base_model(input_ids=input_ids, attention_mask=attention_mask)
            cls_output = outputs.last_hidden_state[:, 0, :]
            normalized_output = self.layer_norm(cls_output)
            output = self.dropout(normalized_output)
            output = self.classifier(output)
            return output

except ImportError:
    # torch가 없는 경우 무시
    pass


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
