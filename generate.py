import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import transformers


class LLM:
    def __init__(self, model_name="mistralai/Mistral-7B-Instruct-v0.1"):
        self.model_name = model_name

        bnb_config = transformers.BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
        )

        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            load_in_4bit=True,
            torch_dtype=torch.bfloat16,
            quantization_config=bnb_config,
        )

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.tokenizer.bos_token_id = 1
        self.stop_token_ids = [0]

    def __call__(self, prompt):
        encoded = self.tokenizer(prompt, return_tensors="pt", add_special_tokens=False)
        model_input = encoded
        generated_ids = self.model.generate(
            **model_input, max_new_tokens=200, do_sample=True
        )
        decoded = self.tokenizer.batch_decode(generated_ids)
        return decoded[0]