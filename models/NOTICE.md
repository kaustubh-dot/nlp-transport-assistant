# Model attribution

MuRIL is a BERT model released by Google as [`google/muril-base-cased`](https://huggingface.co/google/muril-base-cased) under Apache 2.0. A copy of the license is in [APACHE-2.0.txt](APACHE-2.0.txt).

This project uses the vocabulary and configuration from revision `afd9f36c7923d54e97903922ff1b260d091d202f`. Its encoder had prior transport fine-tuning, and this experiment additionally adapts the final two encoder layers and a nine-class classifier head. The distributed seed encoder removes the unused original classifier and preserves the encoder tensors. The manifest records the original checkpoint hash and the hashes of the distributed files.

Reference: Khanuja et al., [MuRIL: Multilingual Representations for Indian Languages](https://arxiv.org/abs/2103.10730).
