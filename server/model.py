import torch.nn as nn


class Model(nn.Module):
    def __init__(self, input_shape, num_classes):
        super(Model, self).__init__()

        # LSTM
        self.lstm1 = nn.LSTM(input_size=10, hidden_size=64, num_layers=1, batch_first=True, bidirectional=False)
        self.lstm2 = nn.LSTM(input_size=64, hidden_size=128, num_layers=1, batch_first=True, bidirectional=False)
        self.lstm3 = nn.LSTM(input_size=128, hidden_size=64, num_layers=1, batch_first=True, bidirectional=False)

        # FC
        # calculate flatten dimension
        self.fc = nn.Sequential(
            nn.Linear(64, 64),
            nn.ReLU(),
            nn.Linear(64, num_classes),
            nn.ReLU(),
        )

        self.flatten = nn.Flatten()
        self.softmax = nn.Softmax(dim=-1)

    def forward(self, x):
        x, _ = self.lstm1(x)
        x, _ = self.lstm2(x)
        x, _ = self.lstm3(x)
        x = self.flatten(x)
        x = self.fc(x)

        x = self.softmax(x)

        return x
