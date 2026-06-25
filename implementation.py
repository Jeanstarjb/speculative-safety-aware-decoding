import torch
import torch.nn.functional as F
import numpy as np

class SpeculativeSafetyAwareDecoding:
    def __init__(self, large_model, small_model, safety_threshold=0.8, alpha=0.5):
        """
        Initialize the Speculative Safety-Aware Decoding (SSD) module.

        Args:
            large_model: The large language model (LLM).
            small_model: The small language model with safety properties.
            safety_threshold: Threshold for match ratio to switch decoding schemes.
            alpha: Weight for combining distributions from large and small models.
        """
        self.large_model = large_model
        self.small_model = small_model
        self.safety_threshold = safety_threshold
        self.alpha = alpha

    def speculative_sampling(self, large_logits, small_logits):
        """
        Combines the logits of the large and small models using a weighted approach.

        Args:
            large_logits: Logits from the large model.
            small_logits: Logits from the small model.

        Returns:
            Combined logits for sampling.
        """
        large_probs = F.softmax(large_logits, dim=-1)
        small_probs = F.softmax(small_logits, dim=-1)
        combined_probs = self.alpha * small_probs + (1 - self.alpha) * large_probs
        return torch.log(combined_probs)

    def compute_match_ratio(self, large_topk, small_topk):
        """
        Computes the match ratio between the top-k tokens of the large and small models.

        Args:
            large_topk: Top-k tokens from the large model.
            small_topk: Top-k tokens from the small model.

        Returns:
            Match ratio as a float.
        """
        match_count = len(set(large_topk).intersection(set(small_topk)))
        return match_count / len(large_topk)

    def decode(self, input_ids, top_k=10):
        """
        Perform Speculative Safety-Aware Decoding.

        Args:
            input_ids: Input token IDs for decoding.
            top_k: Number of top tokens to consider for match ratio computation.

        Returns:
            Decoded token IDs.
        """
        large_logits = self.large_model(input_ids)
        small_logits = self.small_model(input_ids)

        large_topk = torch.topk(large_logits, top_k, dim=-1).indices.squeeze().tolist()
        small_topk = torch.topk(small_logits, top_k, dim=-1).indices.squeeze().tolist()

        match_ratio = self.compute_match_ratio(large_topk, small_topk)

        if match_ratio < self.safety_threshold:
            # Switch to safety-prioritized decoding
            combined_logits = self.speculative_sampling(large_logits, small_logits)
        else:
            # Use large model's logits directly
            combined_logits = large_logits

        # Sample token from the combined logits
        probs = F.softmax(combined_logits, dim=-1)
        sampled_token = torch.multinomial(probs, num_samples=1).item()

        return sampled_token

# Dummy models for demonstration
class DummyModel:
    def __init__(self, vocab_size):
        self.vocab_size = vocab_size

    def __call__(self, input_ids):
        # Generate random logits for demonstration
        batch_size = input_ids.shape[0]
        return torch.randn(batch_size, self.vocab_size)

if __name__ == '__main__':
    # Define dummy models
    vocab_size = 100
    large_model = DummyModel(vocab_size)
    small_model = DummyModel(vocab_size)

    # Initialize SSD
    ssd = SpeculativeSafetyAwareDecoding(large_model, small_model, safety_threshold=0.8, alpha=0.5)

    # Dummy input
    input_ids = torch.tensor([[1, 2, 3]])

    # Decode using SSD
    decoded_token = ssd.decode(input_ids)
    print(f"Decoded token: {decoded_token}")